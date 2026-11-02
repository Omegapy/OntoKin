#!/usr/bin/env python3
"""Concrete pure-scope/contextual/import and fixed-local-rotation inputs."""
from __future__ import annotations
import re
from author_inputs import ROOT, write, manifest, identities, digest, source, tor, span


def main():
    helper='''ontokin "0.21";
module TorqueValues @ "torque-values";
profile "keyed-membership-0.1";

public fn torque @ "torque"(about: Torque) -> Torque {
    return 2 * about;
}
public fn duration @ "duration"() -> Time {
    return 1[s];
}
'''
    write('modules/torque_values.ok',helper)
    baseline=source({'id':'pure','horizon':'2','torques':[tor('drive',0,1,2)]})
    importline='import values @ "values" from "fixture.torque-values" version "1.0.0" digest "'+digest(helper.encode())+'";\n\n'
    local='''public fn torque @ "contextual-torque"(about: Torque, world_z: Time) -> Torque {
    return about;
}

'''
    pure=baseline.replace('scene Demo @ "demo" {',importline+local+'scene Demo @ "demo" {')
    pure=pure.replace('using 2[N*m] for 1[s]','using torque(values.torque(1[N*m]), values.duration()) for values.duration()')
    rows=[]
    def save(name,text,expected,extra_module=False):
        write('sources/'+name+'.ok',text);m=manifest(name)
        if extra_module: m['modules'].append({'package_id':'fixture.torque-values','version':'1.0.0','filename':'torque_values.ok','path':'modules/torque_values.ok'})
        write(name+'.files.json',m)
        rows.append({'id':name,'file_manifest':name+'.files.json','identity':identities(name),'expected':expected,'candidate_observations_used':False})
    save('l01-pure-import-and-contextual-names',pure,{'compile':'accepted','evaluation':'accepted','torque_n_m':2,'duration_seconds':'1','at_1':{'unwrapped_phase':'1','signed_speed':'2'},'at_2':{'unwrapped_phase':'3','signed_speed':'2'},'declaration_semantics':'Imported helper uses its own .21 arithmetic. Local .22 pure function torque and parameters about/world_z remain ordinary identifiers. using/for remain inherited reserved tokens.'},True)
    fixed=baseline.replace('scene Demo @ "demo" {','''public class Flag @ "flag-type" {
    geometry = box(vec3(0.25[m], 0.5[m], 0.125[m]));
    physical = no_body();
}

scene Demo @ "demo" {''')
    fixed=fixed.replace('    at 0[s] sequence {','''    object flag @ "flag": Flag {}
    follow fixed_flag @ "fixed-flag" {
        parent = ball.frame;
        child = flag;
        offset = pose(ball.frame, vec3(0.75[m], 0.375[m], 0[m]), quat(0, 1, 0, 0));
    }
    at 0[s] sequence {''')
    save('l02-nonidentity-fixed-local-rotation',fixed,{'compile':'accepted','evaluation':'accepted','recorded_scope':'eligible fixed-marker path; delivery requires separate1m source variant','flag_local_quaternion_wxyz':[0,1,0,0],'flag_origin_offset_m':['3/4','3/8','0'],'flag_world_quaternion':'(0,cos(theta/2),sin(theta/2),0) for parent world-Z phase theta','flag_origin_formula':['(3/4)cos(theta)-(3/8)sin(theta)','(3/4)sin(theta)+(3/8)cos(theta)','0'],'at_1':{'parent_unwrapped_phase':'1','parent_signed_speed':'2'}})
    # Exact inherited parser errors establish that a source event cannot be
    # converted into an ordinary pure function or initializer side effect.
    event='torque ball @ "illegal" about world_z using 2[N*m] for 1[s];'
    bad_function=baseline.replace('scene Demo @ "demo" {','public fn illegal @ "illegal"() -> Time {\n    '+event+'\n    return 1[s];\n}\n\nscene Demo @ "demo" {')
    save('l03-forbidden-function-event',bad_function,{'compile':'refused','code':'OKL-E-SYNTAX','phase':'syntax','message':"Expected 'return'; found 'torque'.",'primary_source':span(bad_function,'torque',bad_function[:bad_function.index(event)].count('torque')),'authority':'Inherited function_decl requires return after its optional let prefix; no runtime event may execute.'})
    bad_initializer=baseline.replace('scene Demo @ "demo" {','public class Invalid @ "invalid" {\n    '+event+'\n}\n\nscene Demo @ "demo" {')
    at=bad_initializer.index(event)+len('torque ')
    save('l04-forbidden-initializer-event',bad_initializer,{'compile':'refused','code':'OKL-E-SYNTAX','phase':'syntax','message':"Expected '='; found 'ball'.",'primary_source':{'source_id':'entry','start_byte':at,'end_byte':at+4,'text':'ball'},'authority':'Inherited assignment parser treats ordinary torque as a field identifier here and then requires =.'})
    # This module scene is rejected by the existing definition-module rule
    # before any elaboration of its new source event can occur.
    library='''ontokin "0.22";
module LibraryScene @ "library-scene";
profile "torque-0.1";
scene Forbidden @ "forbidden" {
    duration = 1[s];
    at 0[s] sequence { torque absent @ "illegal" about world_z using 1[N*m] for 1[s]; }
}
'''
    write('modules/forbidden_scene.ok',library)
    entry=baseline.replace('scene Demo @ "demo" {','import illegal @ "illegal" from "fixture.forbidden-scene" version "1.0.0" digest "'+digest(library.encode())+'";\n\nscene Demo @ "demo" {')
    name='l05-forbidden-library-scene';write('sources/'+name+'.ok',entry);m=manifest(name);m['modules'].append({'package_id':'fixture.forbidden-scene','version':'1.0.0','filename':'forbidden_scene.ok','path':'modules/forbidden_scene.ok'});write(name+'.files.json',m)
    begin=library.index('scene Forbidden');end=library.rfind('}')+1
    rows.append({'id':name,'file_manifest':name+'.files.json','identity':identities(name),'candidate_observations_used':False,
      'expected':{'compile':'refused','code':'OKL-E-TYPE','phase':'binding','message':'An imported definition module cannot declare a scene.','primary_source':{'source_id':'package:fixture.forbidden-scene@1.0.0','source_revision':digest(library.encode()),'start_byte':begin,'end_byte':end,'text':library[begin:end]},'authority':'Unchanged linker nonentry scene guard precedes unresolved target elaboration.'}})
    # Actual old-profile constructions prove helper, scoped names and fixed
    # local rotation syntax without granting torque to an older importer.
    controls=[]
    for row in rows[:2]:
        original=(ROOT/('sources/'+row['id']+'.ok')).read_text()
        if row['id'].startswith('l01'):
            text=re.sub(r'        torque[^\n]+\n','        force ball @ "pure-control" using vector(world, torque(values.torque(1[N*m]), values.duration()) / 1[m], 0[N], 0[N]) for values.duration();\n',original)
        else:
            text=re.sub(r'        torque[^\n]+\n','',original)
        text=text.replace('"0.22"','"0.21"',1).replace('"torque-0.1"','"keyed-membership-0.1"',1)
        name='control-'+row['id'];write('sources/'+name+'.ok',text);m=manifest(name)
        if row['id'].startswith('l01'):m['modules'].append({'package_id':'fixture.torque-values','version':'1.0.0','filename':'torque_values.ok','path':'modules/torque_values.ok'})
        write(name+'.files.json',m);controls.append({'id':name,'file_manifest':name+'.files.json','identity':identities(name),'expected_compile':'accepted','expected_objects':8 if row['id'].startswith('l01') else 9})
    # Delivery local-rotation case uses the separately selected source request.
    from author_delivery import variant,HOST
    name='delivery-l02-nonidentity-fixed-local-rotation';ident=variant(name,fixed)
    rows[1]['delivery_variant']={'file_manifest':name+'.files.json','identity':ident,'host_policy':HOST,'options':{'fps':4,'end':'2','helpers':True,'position_tolerance_m':0.001,'rotation_tolerance_rad':0.001,'time_tolerance_s':0.000001},'required_future_outcome':'Accepted artifact, independently verified fixed-local-rotation landmark formulas and complete source/certificate history.'}
    write('language-cases.json',{'schema_version':'ontokin.torque-independent-language-cases/1','candidate_output_used':False,'cases':rows,'predecessor_controls':controls,'coverage_limit':'These finite witnesses cover entry event locality, pure imported inputs, inherited contextual-name handling, function/initializer/library-scene exclusions, and fixed local rotations; they do not claim every possible grammar combination.'})


if __name__=='__main__':main()
