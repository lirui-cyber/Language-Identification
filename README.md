# Transformer based Language Identification System
## Configuration environment

Open path.sh file, change MAIN_ROOT to your espnet directory,
```
e.g. MAIN_ROOT=/home3/jicheng/espnet
```
## Data preparation
### Modify the path 
The data folder contains:<br>
- Training set: lre_train [lre17_train_all + lre17_dev_3s + lre17_dev_10s + lre17_dev_30s]
- Test sets: lre17_eval_3s lre17_eval_10s lre17_eval_30s<br>
You can use the ```sed``` command to replace the path in the wav.scp file with your path
```
egs:
Original path: /data/users/ellenrao/NIST_LRE_Corpus/NIST_LRE_2017/LDC2017E22_2017_NIST_Language_Recognition_Evaluation_Training_Data/data/ara-acm/124688.000272.5000.pcm.feather.sph
Your path: /data/NIST_LRE_2017/LDC2017E22_2017_NIST_Language_Recognition_Evaluation_Training_Data/data/ara-acm/124688.000272.5000.pcm.feather.sph
sed -i "s#/data/users/ellenrao/NIST_LRE_Corpus/#/data/#g" data/lre_train/wav.scp
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

#### Organize noise data sets
The noise data sets used to add noise to the test set.
```
rats_data=/home3/andrew219/python_scripts/extract_rats_noise/rats_channels/
mkdir data-16k/rats_channels_AEH_noise
find ${rats_data}/channel_{A,E,H} -name '*.wav' > data-16k/rats_channels_AEH_noise/rats_channels_AEH_noise_file_list.txt
cat data-16k/rats_channels_AEH_noise/rats_channels_AEH_noise_file_list.txt | awk '{ split($0, arr, "/"); c=arr[7]; l=length(arr[8]); name=substr(arr[8], 0, l-4); print name " "name}' >data-16k/rats_channels_AEH_noise/utt2spk
cat data-16k/rats_channels_AEH_noise/rats_channels_AEH_noise_file_list.txt | awk '{ split($0, arr, "/"); c=arr[7]; l=length(arr[8]); name=substr(arr[8], 0, l-4); print name " "$0}' > data-16k/rats_channels_AEH_noise/wav.scp


# fot test set
bash add-noise-for-lid.sh --steps 2 --src-train ../data-16k/lre_eval_3s --noise_dir ../data-16k/rats_noise_channel_AEH
bash add-noise-for-lid.sh --steps 2 --src-train ../data-16k/lre_eval_10s --noise_dir ../data-16k/rats_noise_channel_AEH
bash add-noise-for-lid.sh --steps 2 --src-train ../data-16k/lre_eval_30s --noise_dir ../data-16k/rats_noise_channel_AEH
```
After run "add-noise-for-lid.sh" script, Each folder generates four additional folders.<br>

### Generate new wav file for noise data

You should change this path "/home3/jicheng/lirui/source-data/lre17-16k/" to yourself path.
```
save_16k_dir=/home3/jicheng/lirui/source-data/lre17-16k/
for x in lre17_eval_3s_5_snrs lre17_eval_3s_10_snrs lre17_eval_3s_15_snrs lre17_eval_3s_20_snrs 
         lre17_eval_10s_5_snrs lre17_eval_10s_10_snrs lre17_eval_10s_15_snrs lre17_eval_10s_20_snrs 
         lre17_eval_30s_5_snrs lre17_eval_30s_10_snrs lre17_eval_30s_15_snrs lre17_eval_30s_20_snrs; do
  cat data-16k/$x/wav.scp | 
    awk -v n=$x -v p=$save_16k_dir '{l = length($0); a = substr($0, 0,length-3); print $2" "$3" "$4" "$5" "$6" "$7 " " p "/" n "/" $1 ".wav"}' > data-16k/$x/${x}.cmd
    bash generate_new_wav_cmd.sh $x/$x.cmd
done

for x in lre17_eval_3s lre17_eval_10s lre17_eval_30s;do
    for y in 5 10 15 20;do
        cp data-16k/$x/{utt2spk,wav.scp,utt2lang,spk2utt,reco2dur} data-16k/${x}"_"${y}"_snrs/"
        local=${save_16k_dir}"/"${x}"_"${y}"_snrs/"
        cat data-16k/${x}"_"${y}_snrs/wav.scp | awk -v p=$local '{print $1 " " p "noise-" $1 ".wav"}' > data-16k/${x}"_"${y}_snrs/new_wav.scp
        mv data-16k/${x}"_"${y}_snrs/new_wav.scp data-16k/${x}"_"${y}_snrs/wav.scp
    done
done

```

## Training pipeline
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
