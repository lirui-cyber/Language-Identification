#!/usr/bin

test_sets="lre17_eval_3s_5_snrs lre17_eval_3s_10_snrs lre17_eval_3s_15_snrs lre17_eval_3s_20_snrs lre17_eval_10s_5_snrs lre17_eval_10s_10_snrs lre17_eval_10s_15_snrs lre17_eval_10s_20_snrs lre17_eval_30s_5_snrs lre17_eval_30s_10_snrs lre17_eval_30s_15_snrs lre17_eval_30s_20_snrs "
dump=data-16k
cmd=run.pl
. utils/parse_options.sh
. ./path.sh

for dset in ${test_sets};do
utils/copy_data_dir.sh --validate_opts --non-print data/"${dset}" "$dump/${dset}"
mv $dump/${dset}/wav.scp $dump/${dset}/wav.scp.org
_opts=
 scripts/audio/format_wav_scp.sh --nj 40 --cmd $cmd \
                    --audio-format "wav" --fs "16k" ${_opts} \
                    "$dump/${dset}/wav.scp.org" "$dump/${dset}"


done

