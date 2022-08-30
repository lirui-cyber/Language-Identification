# Transformer based Language Identification System
## Installation:
1. Install Kaldi
```bash
git clone -b 5.4 https://github.com/kaldi-asr/kaldi.git kaldi
cd kaldi/tools/; 
# Run this next line to check for dependencies, and then install them
extras/check_dependencies.sh
make; cd ../src; ./configure; make depend; make
```

2. sph2pipe
```
cd sph2pipe_v2.5
gcc -o sph2pipe *.c -lm

# Add the sph2pipe to the user environment variables
vim ~/.bashrc
export PATH=/home3/jicheng/sph2pipe_v2.5:$PATH
source ~/.bashrc
```
## Download the project
1. Clone the project from GitHub into your workspace
```
git clone -b test_small_set https://github.com/lirui-cyber/Language-Identification.git
```
2. Point to your kaldi <br>
Open ```Language-Identification/path.sh``` file, change **KALDI_ROOT** to your kaldi directory,e.g.
```
KALDI_ROOT=/home/asrxiv/w2021/kaldi-cuda11
```
## Data preparation
The data folder contains:<br>
- **Training set**: lre17_train [ lre17_train_all + lre17_dev_3s + lre17_dev_10s + lre17_dev_30s ]
- **Test sets**: lre17_eval_3s, lre17_eval_10s, lre17_eval_30s<br>
- **Noise Rats data**: rats_noise_channel_AEH,  rats_noise_channel_BCDFG
### Modify the path 
You can use the ```sed``` command to replace the path in the wav.scp file with your path <br>
You only need to change the path of lre17_train, lre17_eval_3s, lre17_eval_10s, lre17_eval_30s to LRE data and rats_noise_channel_AEH, rats_noise_channel_BCDFG to RATS data
```
egs:
Original path: /data/users/ellenrao/NIST_LRE_Corpus/NIST_LRE_2017/LDC2017E22_2017_NIST_Language_Recognition_Evaluation_Training_Data/data/ara-acm/124688.000272.5000.pcm.feather.sph
Your path: /data/NIST_LRE_2017/LDC2017E22_2017_NIST_Language_Recognition_Evaluation_Training_Data/data/ara-acm/124688.000272.5000.pcm.feather.sph
sed -i "s#/data/users/ellenrao/NIST_LRE_Corpus/#/data/#g" data/lre17_train/wav.scp
```

### Run data preparation script
```
  bash prepare_data.sh --steps 1-2
```
## Training pipeline
Before execution, please check the parameters in ```xsa_config``` <br>
You need to change two parameters:<br>
- **userroot**: Project root 
- **model_path**: The path of pretrained-model xlsr_53_56k.pt. <br>
You can download the model from this link below:  https://dl.fbaipublicfiles.com/fairseq/wav2vec/xlsr_53_56k.pt <br>
### Set up Conda environment
```
conda create -n xsa python=3.8 numpy pandas
conda activate xsa
```
- install pytorch
```
conda install pytorch=1.11.0 torchvision torchaudio cudatoolkit=11.3 -c pytorch
```
- install librosa, kaldiio
```
pip install librosa
pip install kaldiio 
```
- install fairseq
```
git clone -b v0.12.2 https://github.com/facebookresearch/fairseq.git  tool/fairseq
pip install -e tool/fairseq
```
- install s3prl
```
git clone -b v0.3.4 https://github.com/s3prl/s3prl.git tool/s3prl
sed -i '60d' tool/s3prl/setup.py
pip install -e tool/s3prl/
mv tool/expert.py tool/s3prl/s3prl/upstream/wav2vec2/
```

### Extracting wav2vec2 features
```
python3 process_lre_data.py
```
### Training 
```
python3 train_xsa.py
```
## Test pipeline
You can change "check_point" variable in xsa_config.json file, Change to the epoch you want to use.
```
python3 test.py
```

## Notice
All the required parameters in the script are written in the xsa_config.json file.
