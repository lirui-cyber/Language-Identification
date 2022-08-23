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
  cp data/$x/{reco2dur,utt2spk,spk2utt,utt2lang,wav.scp} data-16k/$x
  cat data-16k/$x/utt2spk | awk -v p=`pwd`/$save_16k_dir/$x '{print $1 " " p"/"$1".wav"}' > data-16k/$x/wav.scp
  utils/fix_data_dir.sh data-16k/$x
done
```

## Add Noise
In order to test the performance of the system under noisy background, all data sets are denoised.<br>
Different channels of rats data set are used as noise, in which channel A,E,H is used as noise data of test set.

At the same time, different SNR (5, 10, 15, 20) are used for noise addition.<br>
The smaller the SNR, the greater the noise.<br>

### Run add noise scripts
```
# for training data set
cd Add-Noise

bash add-noise-for-lid.sh --steps 2 --src-train ../data-16k/lre17_train --noise_dir ../data/rats_noise_channel_BCDFG

# fot test set
bash add-noise-for-lid.sh --steps 2 --src-train ../data-16k/lre17_eval_3s --noise_dir ../data/rats_noise_channel_AEH
bash add-noise-for-lid.sh --steps 2 --src-train ../data-16k/lre17_eval_10s --noise_dir ../data/rats_noise_channel_AEH
bash add-noise-for-lid.sh --steps 2 --src-train ../data-16k/lre17_eval_30s --noise_dir ../data/rats_noise_channel_AEH
```
After run "add-noise-for-lid.sh" script, Each folder generates four additional folders.<br>
For lre_train, will generate lre_train_5_snrs、lre_train_10_snrs、lre_train_15_snrs、lre_train_20_snrs

### Generate new wav file for noise data
```
save_16k_dir=`pwd`/source-data/lre17-16k
for x in lre_train_5srns lre_train_10srns lre_train_15srns lre_train_20srns 
        lre17_eval_3s_5_snrs lre17_eval_3s_10_snrs lre17_eval_3s_15_snrs lre17_eval_3s_20_snrs 
        lre17_eval_10s_5_snrs lre17_eval_10s_10_snrs lre17_eval_10s_15_snrs lre17_eval_10s_20_snrs 
        lre17_eval_30s_5_snrs lre17_eval_30s_10_snrs lre17_eval_30s_15_snrs lre17_eval_30s_20_snrs; do
  mkdir ${save_16k_dir}/$x 
  cat data-16k/$x/wav.scp | \ 
    awk -v n=$x -v p=$save_16k_dir '{l = length($0); a = substr($0, 0,length-3); print $2" "$3" "$4" "$5" "$6" "$7 " " p "/" n "/" $1 ".wav"}' > data-16k/$x/${x}.cmd
    bash generate_new_wav_cmd.sh data-16k/$x/$x.cmd
done

for x in lre17_eval_3s lre17_eval_10s lre17_eval_30s;do
    for y in 5 10 15 20;do
        cp data-16k/$x/{utt2spk,wav.scp,utt2lang,spk2utt,reco2dur} data-16k/${x}"_"${y}"_snrs/"
        local=${save_16k_dir}"/"${x}"_"${y}"_snrs/"
        cat data-16k/${x}"_"${y}_snrs/wav.scp | awk -v p=$local '{print $1 " " p "noise-" $1 ".wav"}' > data-16k/${x}"_"${y}_snrs/new_wav.scp
        mv data-16k/${x}"_"${y}_snrs/new_wav.scp data-16k/${x}"_"${y}_snrs/wav.scp
    done
done

for x in lre17_train;do
    for y in 5 10 15 20;do
        path=${save_16k_dir}/${x}_${y}_snrs/
        snrs=_${y}_snrs
        rm data-16k/${x}_${y}_snrs/{reco2dur,spk2utt,utt2uniq,wav.scp}
        cat data-16k/${x}_${y}_snrs/utt2lang | awk -v p=$path s=${snrs} '{l=length($1);name=substr($1,7,l);print name s" " p $1".wav"}' > data-16k/${x}_${y}_snrs/wav.scp
        cat data-16k/${x}_${y}_snrs/utt2lang | awk -v p=$path s=${snrs} '{l=length($1);name=substr($1,7,l);print name p" " $2}' > data-16k/${x}_${y}_snrs/utt2spk
        cp data-16k/${x}_${y}_snrs/utt2spk data-16k/${x}_${y}_snrs/utt2lang
        utils/fix_data_dir.sh data-16k/${x}_${y}_snrs/
    done
done
```

## Training pipeline
Before execution, please check the parameters in ```xsa_config``` <br>
### Extracting wav2vec2 features
This script requires the following dependency packages: <br>
numpy, scikit-learn, torch, librosa, kaldiio, s3prl
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
