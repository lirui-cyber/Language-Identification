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

```
### Prepare kaldi format file
Our proposed model aims to use the feature of wav2vec2 model, but the pretrained XLSR-53 wav2vec2 model is trained with 16K data. <br>
Therefore, the aim of this step is to <br>
- Generating real audio from segments (generation of segments files is mentioned in D1 x-vector)
- Upsampling to 16k 
```
# dump: new storage path
bash generate_segments_wav.sh --dump /home3/jicheng/lirui/Language-Identification/data-16k
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
