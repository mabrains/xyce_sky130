comparator.py script compare between xyce and ngspice across dc, op, ac and transient. comparison happens between all devices in skywaterpdk across all corners Currently only dc analysis is supported and only nMOSFETS.

### Usage:
  comparator.py --analysis=\<analysis> [--num_cores=\<num>] options

### Options:
  * -h, --help             Show help text.
  * -v, --version          Show version.
  * --num_cores=\<num>      Number of cores to be used by simulator
  * --analysis=\<analysis>  Required analysis to run valid options are {DC,AC,Transient, OP}

ex: `python comparator.py --analysis=dc --num_cores=8`

## Future work 
Future work is to support AC analysis and support comparison between device parameters in op analysis.

## Issues
- I faced a weired behavior when trying to add AC analysis. I found gain values increases with freq.  
- I wanted to bias every circuit in saturation with AV > 1 to run AC analysis on it. but i don't know how to generally make this happen .