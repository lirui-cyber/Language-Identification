# Transformer based Language Identification System
## Installation:
1. sph2pipe
```
cd sph2pipe_v2.5
gcc -o sph2pipe *.c -lm

# Add the sph2pipe to the user environment variables
vim ~/.bashrc
export PATH=/home3/jicheng/sph2pipe_v2.5:$PATH
source ~/.bashrc
```
## Data preparation
### Modify the path 
The data folder contains:<br>
- **Training set**: lre17_train [ lre17_train_all + lre17_dev_3s + lre17_dev_10s + lre17_dev_30s ]
- **Test sets**: lre17_eval_3s, lre17_eval_10s, lre17_eval_30s<br>
- **Noise Rats data**: rats_noise_channel_AEH,  rats_noise_channel_BCDFG<br>
You can use the ```sed``` command to replace the path in the wav.scp file with your path
```
egs:
Original path: /data/users/ellenrao/NIST_LRE_Corpus/NIST_LRE_2017/LDC2017E22_2017_NIST_Language_Recognition_Evaluation_Training_Data/data/ara-acm/124688.000272.5000.pcm.feather.sph
Your path: /data/NIST_LRE_2017/LDC2017E22_2017_NIST_Language_Recognition_Evaluation_Training_Data/data/ara-acm/124688.000272.5000.pcm.feather.sph
sed -i "s#/data/users/ellenrao/NIST_LRE_Corpus/#/data/#g" data/lre_train/wav.scp
```
### Processing training data
It is to generate each segment as new 16kHz wavefile, which name is the same as the uttID(1st column) of utt2spk
```
python generate_new_wav_cmd.py data/lre17_train/wav.scp data/lre17_train/segments source-data/lre17-16k/lre17_train
```
### Processing test data
Because the test set does not hava segment, only upsampling is required
```
python upsampling_16k.py data/lre17_eval_3s/wav.scp source-data/temp/ source-data/lre17-16k/lre17_eval_3s
python upsampling_16k.py data/lre17_eval_10s/wav.scp source-data/temp/ source-data/lre17-16k/lre17_eval_10s
python upsampling_16k.py data/lre17_eval_30s/wav.scp source-data/temp/ source-data/lre17-16k/lre17_eval_30s
```
### Prepare new kaldi format file
```
save_16k_dir=source-data/lre17-16k
mkdir data-16k
for x in lre17_train lre17_eval_3s lre17_eval_10s lre17_eval_30s;do
  mkdir data-16k/$x
  cp data/$x/{utt2spk,spk2utt,utt2lang,wav.scp} data-16k/$x
  cat data-16k/$x/utt2spk | awk -v p=`pwd`/$save_16k_dir '{print $1 " " p"/"$1".wav"}' > data-16k/$x/wav.scp
  utils/fix_data_dir.sh data-16k/$x
done
```

### Add noise to the test set 
In order to test the performance of the system under noisy background, all data sets are denoised.<br>
Different channels of rats data set are used as noise, in which channel A,E,H is used as noise data of test set.

At the same time, different SNR (5, 10, 15, 20) are used for noise addition.<br>
The smaller the SNR, the greater the noise.<br>

```
# fot test set
bash Add-Noise/add-noise-for-lid.sh --steps 2 --src-train data-16k/lre17_eval_3s --noise_dir data/rats_noise_channel_AEH
bash Add-Noise/add-noise-for-lid.sh --steps 2 --src-train data-16k/lre17_eval_10s --noise_dir data/rats_noise_channel_AEH
bash Add-Noise/add-noise-for-lid.sh --steps 2 --src-train data-16k/lre17_eval_30s --noise_dir data/rats_noise_channel_AEH
```
After run "add-noise-for-lid.sh" script, Each folder generates four additional folders.<br>

### Generate new wav file for noise data
```
bash generate_noise_wav.sh --dump /home3/jicheng/lirui/Language-Identification/data-16k
```

## Training pipeline
Before execution, please check the parameters in ```xsa_config``` <br>
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
