// Official free Khronos glTF validator; preserves the complete issue reports.
const fs=require('fs'),path=require('path'),validator=require('gltf-validator');
(async()=>{
 const sources=JSON.parse(fs.readFileSync('build/g2c4/godot/sources.json'));
 const out='docs/maniqui/g2c4/khronos';fs.mkdirSync(out,{recursive:true});
 const summary={};
 for(const [label,file] of Object.entries(sources)){
  summary[label]={};
  for(const mode of ['master','compat']){
   const p=mode==='master'?file:`build/g2c4/godot/${label}_compat.glb`;
   const report=await validator.validateBytes(new Uint8Array(fs.readFileSync(p)),{uri:path.basename(p),maxIssues:10000});
   fs.writeFileSync(`${out}/${label}_${mode}.json`,JSON.stringify(report,null,2)+'\n');
   const counts={};for(const x of report.issues.messages)counts[x.code]=(counts[x.code]||0)+1;
   summary[label][mode]={errors:report.issues.numErrors,warnings:report.issues.numWarnings,truncated:report.issues.truncated,codes:counts};
  }
 }
 fs.writeFileSync(`${out}/summary.json`,JSON.stringify(summary,null,2)+'\n');console.log(JSON.stringify(summary));
})().catch(e=>{console.error(e);process.exit(1)});
