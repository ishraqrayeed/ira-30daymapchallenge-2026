"""Package this Day 9 site locally. Does not deploy, commit, or push."""
from pathlib import Path
import shutil
P=Path(__file__).resolve().parent
OUT=P/'build'
FILES=['map.html','app.js','cinematic-core.js','style.css','README.md','source-manifest.json','qa-review.json','elevation-check.json','data/nasa-blue-marble.jpg','data/history.json','data/history-footprints.geojson','data/history-changes.geojson']

def main():
 for name in FILES+[str(p.relative_to(P)) for p in (P/'data/history').glob('*.png')]:
  source=P/name;target=OUT/('index.html' if name=='map.html' else name)
  if target.is_symlink() or target.parent.is_symlink():raise ValueError('Refusing to overwrite a symlink')
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
 (OUT/'.nojekyll').touch();print(f'Local static package: {OUT}')
if __name__=='__main__':main()
