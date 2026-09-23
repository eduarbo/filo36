// SPDX-License-Identifier: GPL-3.0-or-later
import {check,normalize} from './config.js';
export const savedKey='flan36.configuration.v1';
const legacyKey='filo36.configuration.v1';
export function restoreConfiguration(storage,catalog){
  let invalid=false;
  for(const key of [savedKey,legacyKey]){
    try{
      const raw=storage.getItem(key);if(!raw)continue;
      if(raw.length>100000)throw Error('Oversized configuration');
      const parsed=JSON.parse(raw);if(check(parsed,catalog).errors.length)throw Error('Invalid configuration');
      const configuration=normalize(parsed,catalog);
      try{storage.setItem(savedKey,JSON.stringify(configuration));}
      catch{return {configuration,message:'Configuration restored. Device storage unavailable; save JSON to keep it.'};}
      return {configuration,message:''};
    }catch{invalid=true;}
  }
  return {configuration:null,message:invalid?'Saved settings could not be loaded. Defaults are available; use JSON to restore.':''};
}
