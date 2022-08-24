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
sed -i "s#/data/users/ellenrao/NIST_LRE_Corpus/#/data/#g" data/lre_train/wav.scp
```
### Processing training data
It is to generate each segment as new 16kHz wavefile, which name is the same as the uttID(1st column) of utt2spk <br>
```source-data``` is the folder where the audio is stored.
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
New kaldi format file are stored in ```data-16k```, and it is better not to change this parameter.
```
bash prepare_new_kaldi_format.sh --save_16k_dir source-data/lre17-16k --data data-16k
```

## Add Noise
In order to test the performance of the system under noisy background, all data sets are denoised.<br>
Different channels of rats data set are used as noise, in which channel A,E,H is used as noise data of test set.

At the same time, different SNR (5, 10, 15, 20) are used for noise addition.<br>
The smaller the SNR, the greater the noise.<br>

### Run add noise scripts
Before running, please make sure you have changed the path of data/{rats_noise_channel_BCDFG,rats_noise_channel_AEH}/wav.scp to the path of your own rats data
```
# for training data set
cd Add-Noise

bash add-noise-for-lid.sh --steps 1-2 --src-train ../data-16k/lre17_train --noise_dir ../data/rats_noise_channel_BCDFG

# fot test set
bash add-noise-for-lid.sh --steps 2 --src-train ../data-16k/lre17_eval_3s --noise_dir ../data/rats_noise_channel_AEH
bash add-noise-for-lid.sh --steps 2 --src-train ../data-16k/lre17_eval_10s --noise_dir ../data/rats_noise_channel_AEH
bash add-noise-for-lid.sh --steps 2 --src-train ../data-16k/lre17_eval_30s --noise_dir ../data/rats_noise_channel_AEH
```
After run "add-noise-for-lid.sh" script, Each folder generates four additional folders.<br>
For lre_train, will generate lre_train_5_snrs、lre_train_10_snrs、lre_train_15_snrs、lre_train_20_snrs

### Generate new wav file for noise data
```
bash generate_wav.sh  --save_16k_dir source-data/lre17-16k --data data-16k
```
## Training pipeline
Before execution, please check the parameters in ```xsa_config``` <br>
You need to change two parameters:<br>
- **userroot**: Project root 
- **model_path**: The path of pretrained-model xlsr_53_56k.pt. <br>
You can download the model from this link below:  https://dl.fbaipublicfiles.com/fairseq/wav2vec/xlsr_53_56k.pt <br>
### Extracting wav2vec2 features
This script requires the following dependency packages: <br>
- numpy
- scikit-learn
- torch
- librosa 
- kaldiio 
- s3prl
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
