#!/bin/bash
#
# just a simple script to save the nccopy command used to save off only the variables needed for testing

rm test_dyamond.nc
ncks -d z,40,41 issi_dyamondv2_replay_c2880_Wp_norway_20200121_0500z.nc test_dyamond.nc
