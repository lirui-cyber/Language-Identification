#!/usr/bin

save_16k_dir=source-data/lre17-16k
mkdir data-16k
for x in lre17_train lre17_eval_3s lre17_eval_10s lre17_eval_30s;do
  mkdir data-16k/$x
  if [ $x = "lre17_train" ];then
    cp data/$x/{utt2spk,spk2utt,utt2lang,wav.scp} data-16k/$x
  else
    cp data/$x/{reco2dur,utt2spk,spk2utt,utt2lang,wav.scp} data-16k/$x
  fi
  cat data-16k/$x/utt2spk | awk -v p=`pwd`/$save_16k_dir/$x '{print $1 " " p"/"$1".wav"}' > data-16k/$x/wav.scp
  utils/fix_data_dir.sh data-16k/$x
done
