#!/bin/bash
#
# just a simple script to save the nccopy command used to save off only the variables needed for testing

rm -f test_dyamond.nc
ncks -d z,38,44,2 issi_dyamondv2_replay_c2880_Tp_norway_20200121_0500z.nc test_dyamond.nc
  # note: indices after "z," are min index, max index, and stride
