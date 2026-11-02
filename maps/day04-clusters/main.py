"""Recompute the reviewed model from the redistributable processed snapshot."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
DAY=Path(__file__).resolve().parent
ROOT=DAY.parents[1]
OUT=ROOT/'data/processed/day04-clusters'

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--clean',action='store_true',help='Reclean downloaded raw caches first (run collect_data.py separately)')
 args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
 if args.clean:
  subprocess.run([sys.executable,str(DAY/'clean_data.py')],check=True)
 else:
  for name in ['manhattan_halal_locations.csv','manhattan_boundary.geojson','day04_audit.json']:
   shutil.copyfile(DAY/name,OUT/name)
 selected=json.loads((DAY/'config.json').read_text())['selected_model']
 subprocess.run([sys.executable,str(DAY/'cluster.py'),'--epsilon',str(selected['epsilon_m']),'--min-samples',str(selected['min_samples'])],check=True)
 for name in ['analyze.py','build_poc.py','validate_poc.py','render.py','validate.py']:
  subprocess.run([sys.executable,str(DAY/name)],check=True)

if __name__=='__main__':main()
