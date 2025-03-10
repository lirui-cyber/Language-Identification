from model.model import *
from model.data_load import *
from score import scoring as scoring
import subprocess
import json

def setup_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    torch.backends.cudnn.deterministic = False
    torch.backends.cudnn.benchmark = False

def validation(valid_txt, valid_feats, model, model_name, device, kaldi, log_dir, num_lang):
    valid_set = RawFeatures2(valid_txt, valid_feats)
    valid_data = DataLoader(dataset=valid_set,
                            batch_size=1,
                            pin_memory=True,
                            shuffle=False,
                            collate_fn=collate_fn_atten)
    model.eval()
    correct = 0
    total = 0
    scores = 0
    with torch.no_grad():
        for step, (utt, labels, seq_len) in enumerate(valid_data):
            utt = utt.to(device=device, dtype=torch.float)
            labels = labels.to(device)
            # Forward pass\
            outputs = model(utt, seq_len)
            predicted = torch.argmax(outputs, -1)
            total += labels.size(-1)
            correct += (predicted == labels).sum().item()
            if step == 0:
                scores = outputs
            else:
                scores = torch.cat((scores, outputs), dim=0)
    acc = correct / total
    print('Current Acc.: {:.4f} %'.format(100 * acc))
    scores = scores.squeeze().cpu().numpy()
    trial_txt = log_dir + '/trial_{}.txt'.format(model_name)
    score_txt = log_dir + '/score_{}.txt'.format(model_name)
    output_txt = log_dir + '/output_{}.txt'.format(model_name)
    scoring.get_trials(valid_txt, num_lang, trial_txt)
    scoring.get_score(valid_txt, scores, num_lang, score_txt)
    eer_txt = trial_txt.replace('trial', 'eer')
    subprocess.call(f"bash ./score/computeEER.sh "
                    f"--write-file {eer_txt} {trial_txt} {score_txt}", shell=True)
    cavg = scoring.compute_cavg(trial_txt, score_txt)
    print("Cavg:{}".format(cavg))
    with open(output_txt, 'w') as f:
        f.write("ACC:{} Cavg:{}".format(acc, cavg))
    return cavg



def main():
    parser = argparse.ArgumentParser(description='paras for making data')
    parser.add_argument('--json', type=str, default='xsa_config.json')
    args = parser.parse_args()
    with open(args.json, 'r') as json_obj:
        config_proj= json.load(json_obj)
    seed = config_proj["optim_config"]["seed"]
    if seed == -1:
        pass
    else:
        setup_seed(seed)
    device = torch.device('cuda:{}'.format(config_proj["optim_config"]["device"])
                          if torch.cuda.is_available() else 'cpu')
    feat_dim = config_proj["model_config"]["d_k"]
    n_heads = config_proj["model_config"]["n_heads"]
    model = X_Transformer_E2E_LID(input_dim=config_proj["model_config"]["feat_dim"],
                                  feat_dim=config_proj["model_config"]["d_k"],
                                  d_k=config_proj["model_config"]["d_k"],
                                  d_v=config_proj["model_config"]["d_k"],
                                  d_ff=config_proj["model_config"]["d_ff"],
                                  n_heads=config_proj["model_config"]["n_heads"],
                                  dropout=0.1,
                                  n_lang=config_proj["model_config"]["n_language"],
                                  max_seq_len=10000)

    model.to(device)
    exp = config_proj["exp"]
    if not os.path.exists(exp):
        os.mkdir(exp)
    model_name = config_proj["model_name"]
    log_dir = config_proj["Input"]["userroot"] + config_proj["Input"]["log"]
    kaldi_root = config_proj["kaldi"]
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    feat_layer = config_proj["wav2vec_info"]["layer"]
    train_txt = config_proj["Input"]["userroot"] + config_proj["Input"]["train_set"] + "/wav2vec_" + config_proj["wav2vec_info"]["model_name"] + ".txt"
    train_feats = config_proj["Input"]["userroot"] + config_proj["Input"]["train_set"] +  "/wav2vec_" + config_proj["wav2vec_info"]["model_name"] + "_" + str(feat_layer) + "_layer/feats.scp"
    train_set = RawFeatures2(train_txt, train_feats)
    train_data = DataLoader(dataset=train_set,
                            batch_size=config_proj["optim_config"]["batch"] ,
                            pin_memory=True,
                            num_workers=config_proj["optim_config"]["num_work"],
                            shuffle=True,
                            collate_fn=collate_fn_atten)

    if config_proj["Input"]["valid_set"] != "none":
        valid_txt = config_proj["Input"]["userroot"] + config_proj["Input"]["valid_set"] + "/wav2vec_" + config_proj["wav2vec_info"]["model_name"] + ".txt"
    else:
        valid_txt = None
    # need to change
    test_sets = config_proj["Input"]["test_sets"].split()

    loss_func_CRE = nn.CrossEntropyLoss().to(device)
    total_step = len(train_data)
    total_epochs = config_proj["optim_config"]["epochs"]
    valid_epochs = config_proj["optim_config"]["valid_epochs"]
    optimizer = torch.optim.Adam(model.parameters(), lr=config_proj["optim_config"]["learning_rate"] )

    if config_proj["optim_config"]["warmup_step"] == -1:
        warmup = total_step*3
    else:
        warmup = config_proj["optim_config"]["warmup_step"]
    warm_up_with_cosine_lr = lambda step: step / warmup \
        if step <= warmup \
        else 0.5 * (math.cos((step - warmup) / (total_epochs * total_step - warmup) * math.pi) + 1)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=warm_up_with_cosine_lr)


    for epoch in tqdm(range(total_epochs)):
        model.train()
        for step, (utt, labels, seq_len) in enumerate(train_data):
            utt_ = utt.to(device=device)
            atten_mask = get_atten_mask(seq_len, utt_.size(0))
            atten_mask = atten_mask.to(device=device)
            mean_mask_, weight_mean = mean_mask(seq_len, len(seq_len), dim= feat_dim * n_heads)
            std_mask_, weight_unbaised = std_mask(seq_len, len(seq_len), dim= feat_dim * n_heads)
            mean_mask_ = mean_mask_.to(device)
            weight_mean = weight_mean.to(device)
            std_mask_ = std_mask_.to(device=device)
            weight_unbaised = weight_unbaised.to(device=device)
            labels = labels.to(device=device)

            # Forward pass
            outputs = model(utt_, seq_len, mean_mask_, weight_mean, std_mask_, weight_unbaised, atten_mask=atten_mask)
            loss_lid = loss_func_CRE(outputs, labels)

            # Backward and optimize
            optimizer.zero_grad()
            loss_lid.backward()
            optimizer.step()
            scheduler.step()
            if step % 200 == 0:
                print("Epoch [{}/{}], Step [{}/{}] Loss: {:.4f} ".
                    format(epoch + 1, total_epochs, step + 1, total_step, loss_lid.item()))

        name = config_proj["exp"] + '/xsa_' + str(epoch) + '.ckpt'
        torch.save(model.state_dict(), name)

            # print(get_lr(optimizer))
        if epoch >= total_epochs - valid_epochs - 1:
        # if epoch >= total_epochs - valid_epochs -1 or epoch == 10:
            if valid_txt is not None:
                valid_feats = config_proj["Input"]["userroot"] + config_proj["Input"]["valid_set"] +  "/wav2vec_" + config_proj["wav2vec_info"]["model_name"] + "_" + str(feat_layer) + "_layer/feats.scp"

                validation(valid_txt, valid_feats, model, model_name, device, kaldi=kaldi_root, log_dir=log_dir,
                    num_lang=config_proj["model_config"]["n_language"])
                    
            for test in test_sets:
                test_txt = config_proj["Input"]["userroot"] + test + "/wav2vec_" + config_proj["wav2vec_info"]["model_name"] + ".txt"
                test_feats = config_proj["Input"]["userroot"] + test +  "/wav2vec_" + config_proj["wav2vec_info"]["model_name"] + "_" + str(feat_layer) + "_layer/feats.scp"

                if test_txt is not None:
                    validation(test_txt, test_feats, model, model_name, device, kaldi=kaldi_root, log_dir=log_dir,
                        num_lang=config_proj["model_config"]["n_language"])


if __name__ == "__main__":
    main()
