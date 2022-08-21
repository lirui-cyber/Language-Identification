#!/usr/bin

train_set=lre17_train
test_sets="lre17_eval_3s lre17_eval_10s lre17_eval_30s"
dump=data-16k
cmd=run.pl
. utils/parse_options.sh
. ./path.sh

for dset in "${train_set}" ${test_sets};do
utils/copy_data_dir.sh --validate_opts --non-print data/"${dset}" "$dump/${dset}"
rm -f $dump/${dset}/{segments,wav.scp}
_opts=
if [ -e data/"${dset}"/segments ];then
    _opts+="--segments data/${dset}/segments "
fi
 scripts/audio/format_wav_scp.sh --nj 40 --cmd $cmd \
                    --audio-format "wav" --fs "16k" ${_opts} \
                    "data/${dset}/wav.scp" "$dump/${dset}"


done

