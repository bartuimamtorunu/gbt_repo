import maya.cmds as cmds
import maya.mel as mel
import math, os, re

class MayaPowerToolsUI(object):
    def __init__(self):
        self.win_id = "mayaPowerToolsUI"
        self.colors = {'bg': [0.12, 0.12, 0.12], 'head': [0.2, 0.2, 0.2], 'btn': [0.25, 0.25, 0.25], 'lime': [0.5, 0.7, 0.17], 'red': [0.8, 0.25, 0.25], 'blue': [0.2, 0.6, 0.8], 'org': [0.8, 0.4, 0.2]}
        self.grid_sel = []

        if cmds.window(self.win_id, ex=True): cmds.deleteUI(self.win_id)
        self.window = cmds.window(self.win_id, title="MPT v16.4 FINAL FIX", wh=(340, 1000), bgc=self.colors['bg'])

        main = cmds.formLayout()
        scroll = cmds.scrollLayout(cr=True)
        cmds.formLayout(main, e=True, af=[(scroll, k, 0) for k in ['top','left','bottom','right']])
        self.layout = cmds.columnLayout(adj=True, rs=2, p=scroll)

        self.build_ui()
        cmds.showWindow(self.window)
        self.toggle_match_ui()

    def _frame(self, lbl):
        cmds.setParent(self.layout); cmds.separator(h=5, style='none')
        cmds.frameLayout(l=" "+lbl.upper(), cll=True, bgc=self.colors['head'], fn='boldLabelFont', mw=4, mh=4)
        return cmds.columnLayout(adj=True, rs=2)

    def _btn(self, lbl, cmd, bg=None, tip=""):
        cmds.button(l=lbl, c=cmd, bgc=bg if bg else self.colors['btn'], h=28, ann=tip)

    def build_ui(self):
        self._frame("1. Object Prep")
        self._btn("Freeze & History", self.freeze_history, self.colors['lime'])
        self._btn("Smart Freeze (Pivot)", self.smart_freeze)
        cmds.rowLayout(nc=2, cw2=(150,150), cl2=('center','center'))
        cmds.button(l="Drop Floor", w=146, h=28, bgc=self.colors['btn'], c=self.drop_floor)
        cmds.button(l="To Origin", w=146, h=28, bgc=self.colors['btn'], c=self.to_origin)
        cmds.setParent('..')
        self._btn("Clear Nodes", self.clear_nodes, self.colors['red'])
        cmds.separator(h=5, st='in')
        self._btn("GLOBAL MATERIAL FIX", self.global_fix, self.colors['org'])
        cmds.setParent('..')

        self._frame("2. Pivot & Align")
        cmds.gridLayout(nc=3, cwh=(100,28), cr=True)
        pivs = [('Top L',-1,1),('Top',0,1),('Top R',1,1),('Left',-1,0),('Center',0,0),('Right',1,0),('Bot L',-1,-1),('Bottom',0,-1),('Bot R',1,-1)]
        for l,x,y in pivs: cmds.button(l=l, bgc=self.colors['lime'] if l=="Center" else self.colors['btn'], c=lambda _,a=x,b=y: self.set_pivot(a,b))
        cmds.setParent('..')
        cmds.rowLayout(nc=3, cw3=(98,98,98))
        for ax in 'xyz': cmds.button(l="Align "+ax.upper(), w=98, h=28, bgc=self.colors['btn'], c=lambda _,a=ax: self.align_obj(a))
        cmds.setParent('..')
        cmds.setParent('..')

        self._frame("3. FBX Importer")
        self.txt_imp_path = cmds.textFieldButtonGrp(l="Path:", bl="..", cw3=(40, 200, 30), adj=2, bc=lambda: self.browse(self.txt_imp_path))
        cmds.rowLayout(nc=2, cw2=(80, 200))
        cmds.text(l="Obj Prefix:", al="right")
        self.txt_imp_prefix = cmds.textField(tx="SM_", w=150, ann="Prefix for imported Objects.")
        cmds.setParent('..')
        self.chk_ren_disk = cmds.checkBox(l="Rename Disk Files", v=True, ann="Renames .png files to T_Name_BC.png")
        cmds.text(l="Logic: FORCE FBX Filename for Everything", al="center", fn="smallPlainLabelFont")
        self.prog_imp = cmds.progressBar(maxValue=100, h=8)
        self._btn("IMPORT FBX & PROCESS", self.do_import, self.colors['lime'])
        cmds.setParent('..')

        self._frame("4. Texture Matcher")
        cmds.rowLayout(nc=3, cw3=(96, 96, 96))
        self.chk_sel = cmds.checkBox(l="Sel Only", v=True)
        self.chk_sub = cmds.checkBox(l="Sub-Dir", v=True)
        self.chk_adv = cmds.checkBox(l="Rules", v=False, cc=self.toggle_match_ui)
        cmds.setParent('..')
        self.lay_match = cmds.columnLayout(vis=False, adj=True)
        self.txt_pre = cmds.textFieldGrp(l="Mat Pre:", tx="MI_", cw2=(60,100))
        defs = [('Diff','_D,_BC,_color,_basecolor'),('Norm','_N,_Normal,_normal'),('Rough','_R,_Roughness'),('Metal','_M,_Metalness')]
        for k,v in defs: setattr(self, 'ui_suff_'+k.lower(), cmds.textFieldGrp(l=k+':', tx=v, cw2=(40,200), adj=2))
        cmds.setParent('..')
        self.txt_tex_path = cmds.textFieldButtonGrp(l="Path:", bl="..", cw3=(40, 200, 30), adj=2, bc=lambda: self.browse(self.txt_tex_path))
        cmds.rowLayout(nc=2, cw2=(150,140))
        self.rad_logic = cmds.radioButtonGrp(l="", la2=['Num', 'Name'], nrb=2, sl=2, cw3=(0,54,54), cc=self.toggle_match_ui)
        self.rad_type = cmds.radioButtonGrp(l="", la4=['Bl','Ph','Lm','Ar'], nrb=4, sl=4, cw5=(0,30,30,30,30))
        cmds.setParent('..')
        self._btn("AUTO MATCH & ASSIGN", self.match_textures, self.colors['lime'])
        cmds.setParent('..')

        self._frame("5. Grid Arranger")
        self.chk_grid_rt = cmds.checkBox(l="Real-Time", cc=self.grid_toggle)
        self.sl_col = cmds.intSliderGrp(l='Cols:', min=1, max=50, v=5, f=1, dc=self.grid_upd, cc=self.grid_upd, cw3=(40,40,100))
        self.sl_sx = cmds.floatSliderGrp(l='Sp X:', min=0, max=1000, v=20, f=1, dc=self.grid_upd, cc=self.grid_upd, cw3=(40,40,100))
        self.sl_sy = cmds.floatSliderGrp(l='Sp Y:', min=0, max=1000, v=20, f=1, dc=self.grid_upd, cc=self.grid_upd, cw3=(40,40,100))
        self._btn("Arrange", self.do_grid, self.colors['lime'])
        cmds.setParent('..')

        self._frame("6. FBX Batch Exporter")
        self.txt_exp_path = cmds.textFieldButtonGrp(l="Out Path:", bl="..", cw3=(60, 200, 30), adj=2, bc=lambda: self.browse(self.txt_exp_path))
        cmds.text(l="Logic: Select Objects -> Click Export", al="center", fn="smallPlainLabelFont")
        cmds.text(l="Structure: Path/SM_Name/SM_Name.fbx (Embedded)", al="center", fn="smallPlainLabelFont")
        self.prog_exp = cmds.progressBar(maxValue=100, h=8)
        self._btn("BATCH EXPORT (SM_...)", self.do_export, self.colors['org'])
        cmds.setParent('..')

        self._frame("7. Smart Renamer")
        self.ui_ren_mode = cmds.radioButtonGrp(l="Mode:", la3=['Scene', 'Disk', 'Materials'], nrb=3, sl=1, cw4=(45,60,60,60), cc=self.toggle_ren_path)
        self.lay_ren_path = cmds.columnLayout(vis=False, adj=True)
        self.txt_ren_disk_path = cmds.textFieldButtonGrp(l="Path:", bl="..", cw3=(40, 200, 30), adj=2, bc=lambda: self.browse(self.txt_ren_disk_path))
        cmds.setParent('..')
        cmds.separator(h=5, st='in')
        self.ui_ren_find = cmds.textFieldGrp(l="Find:", cw2=(60,200), adj=2)
        self.ui_ren_rep  = cmds.textFieldGrp(l="Replace:", cw2=(60,200), adj=2)
        self.ui_ren_pre  = cmds.textFieldGrp(l="Prefix:", cw2=(60,200), adj=2)
        self.ui_ren_suf  = cmds.textFieldGrp(l="Suffix:", cw2=(60,200), adj=2)
        cmds.separator(h=5, st='in')
        cmds.text("Numerical Rename (Optional)", fn='smallPlainLabelFont', al='center')
        self.ui_ren_base = cmds.textFieldGrp(l="Base Name:", cw2=(70,180), adj=2, ann="If filled, renames to Name_01, Name_02...")
        self.ui_ren_pad  = cmds.intFieldGrp(l="Padding:", v1=2, cw2=(70,50))
        cmds.separator(h=5, st='none')
        self._btn("EXECUTE SMART RENAME", self.run_renamer, self.colors['lime'])
        self._btn("RENAME MAT TO OBJ", self.ren_mat_obj, self.colors['blue'], tip="Matches selected object's material name to its own name")
        cmds.setParent('..')

        self._frame("Material Tools")
        self.rad_conv = cmds.radioButtonGrp(l="To:", la3=['Blinn', 'Lamb', 'Arn'], nrb=3, sl=3, cw4=(30,60,60,60))
        self._btn("Convert Material", self.convert_mats, self.colors['lime'])
        cmds.rowLayout(nc=3, cw3=(98,98,98))
        for m, c in [('Norm', self.colors['red']), ('Rough', None), ('Metal', None)]:
            cmds.button(l="Brk "+m, bgc=c if c else self.colors['btn'], w=96, c=lambda x,mode=m.lower(): self.break_conn(mode))
        cmds.setParent('..')
        cmds.setParent('..')

        self._frame("Baking")
        desk = os.path.join(os.path.expanduser("~"), "Desktop").replace("\\", "/")
        self.txt_bake = cmds.textFieldButtonGrp(l="Out:", bl="..", tx=desk, cw3=(40, 200, 30), adj=2, bc=lambda: self.browse(self.txt_bake))
        self._btn("Bake AO (Arnold)", self.bake_ao, self.colors['lime'])
        cmds.setParent('..')

    def browse(self, field):
        f = cmds.fileDialog2(fm=3);
        if f: cmds.textFieldButtonGrp(field, e=True, tx=f[0])

    def toggle_match_ui(self, *args): cmds.columnLayout(self.lay_match, e=True, vis=(cmds.radioButtonGrp(self.rad_logic, q=1, sl=1)==2 and cmds.checkBox(self.chk_adv, q=1, v=1)))
    def toggle_ren_path(self, *args): cmds.columnLayout(self.lay_ren_path, e=True, vis=(cmds.radioButtonGrp(self.ui_ren_mode, q=1, sl=1) == 2))

    def freeze_history(self, *args):
        cmds.undoInfo(openChunk=True)
        try: cmds.makeIdentity(a=1, t=1, r=1, s=1, n=0); cmds.delete(ch=1)
        finally: cmds.undoInfo(closeChunk=True)

    def smart_freeze(self, *args):
        cmds.undoInfo(openChunk=True)
        try:
            for o in cmds.ls(sl=1):
                p = cmds.xform(o, q=1, ws=1, rp=1)
                cmds.move(0,0,0, o, rpr=1); cmds.makeIdentity(o, a=1, t=1, r=1, s=1)
                cmds.move(p[0], p[1], p[2], o, rpr=1)
        finally: cmds.undoInfo(closeChunk=True)

    def drop_floor(self, *args):
        cmds.undoInfo(openChunk=True)
        try:
            for o in cmds.ls(sl=1):
                bb = cmds.xform(o, q=1, bb=1, ws=1)
                cmds.move(0, -bb[1], 0, o, r=1, ws=1)
        finally: cmds.undoInfo(closeChunk=True)

    def to_origin(self, *args):
        cmds.undoInfo(openChunk=True)
        try:
            for o in cmds.ls(sl=1): cmds.move(0,0,0, o, a=1, rpr=1)
        finally: cmds.undoInfo(closeChunk=True)

    def clear_nodes(self, *args):
        mel.eval('hyperShadePanelMenuCommand("hyperShadePanel1", "deleteUnusedNodes");')
        empty = [g for g in cmds.ls(type='transform') if not cmds.listRelatives(g, c=1) and not cmds.listRelatives(g, s=1)]
        if empty: cmds.delete(empty)

    def set_pivot(self, x, y):
        cmds.undoInfo(openChunk=True)
        try:
            for o in cmds.ls(sl=1):
                bb = cmds.xform(o, q=1, bb=1, ws=1)
                px = bb[0] if x==-1 else (bb[3] if x==1 else (bb[0]+bb[3])/2.0)
                py = bb[1] if y==-1 else (bb[4] if y==1 else (bb[1]+bb[4])/2.0)
                pz = (bb[2]+bb[5])/2.0
                cmds.xform(o, piv=(px,py,pz), ws=1)
        finally: cmds.undoInfo(closeChunk=True)

    def align_obj(self, ax):
        sel = cmds.ls(sl=1)
        if len(sel)<2: return
        cmds.undoInfo(openChunk=True)
        try:
            i = {'x':0,'y':1,'z':2}[ax]
            tgt = cmds.xform(sel[-1], q=1, bb=1, ws=1); t_c = (tgt[i]+tgt[i+3])/2.0
            for o in sel[:-1]:
                cur = cmds.xform(o, q=1, bb=1, ws=1); d = t_c - (cur[i]+cur[i+3])/2.0
                cmds.move(d if i==0 else 0, d if i==1 else 0, d if i==2 else 0, o, r=1, ws=1)
        finally: cmds.undoInfo(closeChunk=True)

    def run_renamer(self, *args):
        mode = cmds.radioButtonGrp(self.ui_ren_mode, q=1, sl=1)
        find_s = cmds.textFieldGrp(self.ui_ren_find, q=1, tx=1)
        rep_s  = cmds.textFieldGrp(self.ui_ren_rep, q=1, tx=1)
        pre    = cmds.textFieldGrp(self.ui_ren_pre, q=1, tx=1)
        suf    = cmds.textFieldGrp(self.ui_ren_suf, q=1, tx=1)
        base   = cmds.textFieldGrp(self.ui_ren_base, q=1, tx=1)
        pad    = cmds.intFieldGrp(self.ui_ren_pad, q=1, v1=1)

        if mode == 2: # DISK RENAME
            path = cmds.textFieldButtonGrp(self.txt_ren_disk_path, q=1, tx=1)
            if not os.path.isdir(path): return cmds.warning("Invalid Disk Path")
            files = sorted(os.listdir(path))
            for i, f in enumerate(files):
                b_name, ext = os.path.splitext(f)
                new_b = self._calc_name(b_name, i, base, pad, pre, suf, find_s, rep_s)
                if f != (new_b + ext): os.rename(os.path.join(path, f), os.path.join(path, new_b + ext))
            print("Disk Rename Complete")
            return

        targets = []
        if mode == 1: targets = cmds.ls(sl=1, l=True)
        else:
            for o in cmds.ls(sl=1):
                sh = cmds.listRelatives(o, s=1)
                if sh:
                    sg = cmds.listConnections(sh[0], type='shadingEngine')
                    if sg:
                        m = cmds.listConnections(sg[0] + ".surfaceShader")
                        if m: targets.append(m[0])
            targets = list(set(targets))

        if not targets: return cmds.warning("No targets selected")
        cmds.undoInfo(openChunk=True)
        try:
            for i, obj in enumerate(targets):
                if not cmds.objExists(obj): continue
                short = obj.split("|")[-1].split(":")[-1]
                new = self._calc_name(short, i, base, pad, pre, suf, find_s, rep_s)
                cmds.rename(obj, new)
        finally: cmds.undoInfo(closeChunk=True)

    def _calc_name(self, current, idx, base, pad, pre, suf, find, rep):
        res = current
        if base: res = "{}_{:0{}d}".format(base, idx+1, pad)
        if find: res = res.replace(find, rep)
        return pre + res + suf

    def ren_mat_obj(self, *args):
        cmds.undoInfo(openChunk=True)
        try:
            for o in cmds.ls(sl=1):
                sh = cmds.listRelatives(o, s=1)
                if sh:
                    sg = cmds.listConnections(sh[0], type='shadingEngine')
                    if sg:
                        m = cmds.listConnections(sg[0]+".surfaceShader")
                        if m and m[0] not in ['lambert1','standardSurface1']:
                            cmds.rename(m[0], "MI_" + o.split('|')[-1].split(':')[-1])
        finally: cmds.undoInfo(closeChunk=True)

    def grid_toggle(self, v): self.grid_sel = cmds.ls(sl=1, l=1) if v else []; self.grid_upd()
    def grid_upd(self, *a):
        if self.grid_sel: self.do_grid(use_cached=True)
    def do_grid(self, use_cached=False):
        sel = self.grid_sel if use_cached else cmds.ls(sl=1, l=1)
        if not sel: return
        cmds.undoInfo(openChunk=True)
        try:
            sel.sort(); cols = cmds.intSliderGrp(self.sl_col, q=1, v=1)
            sx, sy = cmds.floatSliderGrp(self.sl_sx, q=1, v=1), cmds.floatSliderGrp(self.sl_sy, q=1, v=1)
            ws, hs = [0]*cols, [0]*int(math.ceil(len(sel)/float(cols)))
            bbs = [cmds.xform(o, q=1, bb=1, ws=1) for o in sel]
            for i, bb in enumerate(bbs):
                ws[i%cols] = max(ws[i%cols], bb[3]-bb[0])
                hs[i//cols] = max(hs[i//cols], bb[5]-bb[2])
            x_c, z_c = 0, 0
            for i, o in enumerate(sel):
                r, c = i // cols, i % cols
                if c==0: x_c = 0; z_c += (hs[r-1] + sy) if r>0 else 0
                bb = bbs[i]
                cmds.move(x_c - bb[0], 0, -z_c - bb[5], o, r=1, ws=1)
                x_c += ws[c] + sx
        finally: cmds.undoInfo(closeChunk=True)

    def _has_exportable_content(self, obj):
        shapes = cmds.listRelatives(obj, s=1, ni=1, f=1) or []
        desc_shapes = cmds.listRelatives(obj, ad=1, s=1, ni=1, f=1) or []
        all_shapes = shapes + desc_shapes
        valid_types = {'mesh', 'nurbsSurface', 'subdiv', 'joint'}
        for sh in all_shapes:
            if cmds.nodeType(sh) in valid_types:
                return True
        return False

    def do_export(self, *args):
        if not cmds.pluginInfo('fbxmaya', q=True, loaded=True):
            try:
                cmds.loadPlugin('fbxmaya')
            except:
                return cmds.warning("FBX Plugin (fbxmaya) could not be loaded. Please check Plug-in Manager.")

        try:
            mel.eval('source "fbxmaya.mel"')
        except:
            pass

        if mel.eval('exists "FBXExportEmbedMedia"'):
            mel.eval("FBXExportEmbedMedia -v true;")
        else:
            cmds.warning("FBXExportEmbedMedia not found. Export will continue without embedded media option.")

        if mel.eval('exists "FBXExportSmoothingGroups"'):
            mel.eval("FBXExportSmoothingGroups -v true;")
        if mel.eval('exists "FBXExportTangents"'):
            mel.eval("FBXExportTangents -v true;")
        if mel.eval('exists "FBXExportTriangulate"'):
            mel.eval("FBXExportTriangulate -v false;")

        if mel.eval('exists "FBXExportInputConnections"'):
            mel.eval("FBXExportInputConnections -v true;")
        if mel.eval('exists "FBXExportEmbeddedTextures"'):
            mel.eval("FBXExportEmbeddedTextures -v true;")

        path = cmds.textFieldButtonGrp(self.txt_exp_path, q=1, tx=1)
        if not path or not os.path.isdir(path): return cmds.warning("Select Output Folder")

        sel = cmds.ls(sl=1, l=1)
        if not sel: return cmds.warning("Select objects to export")

        cmds.progressBar(self.prog_exp, e=True, bp=True, maxValue=len(sel))

        skipped = []
        for obj in sel:
            if not self._has_exportable_content(obj):
                skipped.append(obj)
                cmds.progressBar(self.prog_exp, e=True, step=1)
                continue

            short = obj.split("|")[-1].split(":")[-1]
            clean_name = re.sub(r'^(SM_|T_|M_)', '', short, flags=re.I)

            export_name = "SM_" + clean_name
            final_file = os.path.join(path, export_name + ".fbx").replace("\\", "/")

            cmds.select(cl=1)
            cmds.select(obj, r=1)
            cmds.select(obj, hi=1, add=1)

            print("Exporting: " + final_file)

            safe_file = final_file.replace('"', '\\"')
            mel.eval('FBXExport -f "{}" -s;'.format(safe_file))

            cmds.progressBar(self.prog_exp, e=True, step=1)

        cmds.select(sel)
        cmds.progressBar(self.prog_exp, e=True, ep=True)

        if skipped:
            cmds.warning("Skipped objects with no exportable shape: {}".format(', '.join([s.split('|')[-1] for s in skipped])))
        print("Batch Export Complete!")

    def match_textures(self, *args):
        fold = cmds.textFieldButtonGrp(self.txt_tex_path, q=1, tx=1)
        if not fold: return cmds.warning("Select folder")
        cmds.undoInfo(openChunk=True)
        try:
            logic = cmds.radioButtonGrp(self.rad_logic, q=1, sl=1)
            suffs = {k: [x.strip() for x in cmds.textFieldGrp(getattr(self, 'ui_suff_'+k), q=1, tx=1).split(',') if x.strip()] for k in ['diff','norm','rough','metal']}
            files = {}
            valid = ['.png','.jpg','.jpeg','.tif','.tiff','.tga','.exr','.psd','.bmp']
            file_list = []
            if cmds.checkBox(self.chk_sub, q=1, v=1):
                for root, _, fs in os.walk(fold):
                    for f in fs: file_list.append((root, f))
            else:
                for f in os.listdir(fold): file_list.append((fold, f))

            for root, f in file_list:
                if os.path.splitext(f)[1].lower() in valid:
                    base = os.path.splitext(f)[0]
                    k_obj, k_type = None, 'diff'
                    found_type = False
                    for t, ss in suffs.items():
                        if found_type: break
                        for s in ss:
                            if base.endswith(s): k_type = t; base = base[:-len(s)]; found_type=True; break
                    base = re.sub(r'^(T_|SM_|M_|Tex_)', '', base, flags=re.I)
                    if logic == 1:
                        nums = re.findall(r'\d+', base)
                        if nums: k_obj = nums[-1].zfill(2)
                    else: k_obj = base.lower()
                    if k_obj:
                        if k_obj not in files: files[k_obj] = {}
                        files[k_obj][k_type] = os.path.join(root, f).replace("\\","/")

            m_pre = cmds.textFieldGrp(self.txt_pre, q=1, tx=1)
            typ = ['blinn','phong','lambert','aiStandardSurface'][cmds.radioButtonGrp(self.rad_type, q=1, sl=1)-1]
            targets = cmds.ls(sl=1) if cmds.checkBox(self.chk_sel, q=1, v=1) else cmds.ls(type='transform')
            for o in targets:
                name = o.split('|')[-1].split(':')[-1]
                key = (re.findall(r'\d+', name)[-1].zfill(2) if re.findall(r'\d+', name) else None) if logic==1 else name.lower()
                if key and key in files: self.create_mat(o, m_pre+name, typ, files[key])
        finally: cmds.undoInfo(closeChunk=True)

    def create_mat(self, obj, name, typ, maps):
        if cmds.objExists(name): cmds.delete(name)
        sh = cmds.shadingNode(typ, asShader=1, n=name)
        sg = cmds.sets(n=name+"SG", empty=1, renderable=1, noSurfaceShader=1)
        cmds.connectAttr(sh+".outColor", sg+".surfaceShader")
        cmds.sets(obj, e=1, fe=sg)
        p2d = cmds.shadingNode('place2dTexture', asUtility=1)
        for k, path in maps.items():
            f = cmds.shadingNode('file', asTexture=1)
            cmds.setAttr(f+".fileTextureName", path, type='string')
            cmds.connectAttr(p2d+".outUV", f+".uvCoord")
            if k in ['norm', 'rough', 'metal']:
                cmds.setAttr(f + ".ignoreColorSpaceFileRules", 1)
                cmds.setAttr(f + ".colorSpace", "Raw", type="string")
            if typ == 'aiStandardSurface':
                if k=='diff': cmds.connectAttr(f+".outColor", sh+".baseColor")
                elif k=='norm':
                    n = cmds.shadingNode('aiNormalMap', asUtility=1)
                    cmds.connectAttr(f+".outColor", n+".input"); cmds.connectAttr(n+".outValue", sh+".normalCamera")
                elif k in ['rough','metal']:
                    cmds.setAttr(f+".alphaIsLuminance", 1)
                    dest = ".specularRoughness" if k=='rough' else ".metalness"
                    cmds.connectAttr(f+".outAlpha", sh+dest)
            elif typ in ['blinn','phong']:
                if k=='diff': cmds.connectAttr(f+".outColor", sh+".color")
                elif k=='norm':
                    b = cmds.shadingNode('bump2d', asUtility=1); cmds.setAttr(b+".bumpInterp", 1)
                    cmds.connectAttr(f+".outAlpha", b+".bumpValue"); cmds.connectAttr(b+".outNormal", sh+".normalCamera")

    def do_import(self, *args):
        if not cmds.pluginInfo('fbxmaya', q=True, loaded=True):
            try: cmds.loadPlugin('fbxmaya')
            except: pass

        fold = cmds.textFieldButtonGrp(self.txt_imp_path, q=1, tx=1)
        if not fold or not os.path.isdir(fold):
            cmds.warning("Invalid Path")
            return

        user_prefix = cmds.textField(self.txt_imp_prefix, q=1, tx=1)
        do_rename_disk = cmds.checkBox(self.chk_ren_disk, q=1, v=1)

        fbxs = [f for f in os.listdir(fold) if f.lower().endswith(".fbx")]

        cmds.progressBar(self.prog_imp, e=True, bp=True, maxValue=len(fbxs))
        cmds.undoInfo(openChunk=True)
        try:
            for f in fbxs:
                base = os.path.splitext(f)[0]
                full_path = os.path.join(fold, f).replace("\\", "/")

                clean_base = re.sub(r'^(SM_|T_|M_|SK_)', '', base, flags=re.I)
                print(">>> Importing: " + f + " | Forced Name: " + clean_base)

                nodes = cmds.file(full_path, i=True, type="FBX", returnNewNodes=True)
                if not nodes: continue

                files = [n for n in nodes if cmds.objExists(n) and cmds.nodeType(n) == 'file']
                for file_node in files:
                    if not cmds.objExists(file_node): continue

                    suffix = "BC"
                    is_raw = False

                    try:
                        dests = cmds.listConnections(file_node, plugs=True, source=False, destination=True) or []
                        for d in dests:
                            attr = d.lower()
                            if "bump" in attr or "normal" in attr: suffix = "N"; is_raw = True
                            elif "specular" in attr or "roughness" in attr: suffix = "R"; is_raw = True
                            elif "metal" in attr or "reflect" in attr: suffix = "M"; is_raw = True
                    except: pass

                    new_tex_name = "T_{}_{}".format(clean_base, suffix)

                    try:
                        renamed = cmds.rename(file_node, new_tex_name)
                        if is_raw:
                            cmds.setAttr(renamed + ".ignoreColorSpaceFileRules", 1)
                            cmds.setAttr(renamed + ".colorSpace", "Raw", type="string")

                        if do_rename_disk:
                            old_path = cmds.getAttr(renamed + ".fileTextureName")
                            if old_path and os.path.isfile(old_path):
                                d_dir = os.path.dirname(old_path)
                                d_ext = os.path.splitext(old_path)[1]
                                new_filename = new_tex_name + d_ext
                                new_full_path = os.path.join(d_dir, new_filename).replace("\\", "/")

                                if old_path != new_full_path and not os.path.exists(new_full_path):
                                    try:
                                        os.rename(old_path, new_full_path)
                                        cmds.setAttr(renamed + ".fileTextureName", new_full_path, type="string")
                                        print("Disk Rename: " + new_filename)
                                    except: pass
                                elif os.path.exists(new_full_path):
                                    cmds.setAttr(renamed + ".fileTextureName", new_full_path, type="string")
                    except: pass

                sgs = [n for n in nodes if cmds.objExists(n) and cmds.nodeType(n) == 'shadingEngine']
                for sg in sgs:
                    if sg in ["initialShadingGroup", "initialParticleSE"]: continue
                    if not cmds.objExists(sg): continue
                    try:
                        mats = cmds.listConnections(sg + ".surfaceShader")
                        if mats and cmds.objExists(mats[0]):
                            cmds.rename(mats[0], "MI_" + clean_base)
                    except: pass

                transforms = [n for n in nodes if cmds.objExists(n) and cmds.nodeType(n) == 'transform']
                roots = [t for t in transforms if not cmds.listRelatives(t, p=True)]
                for r in roots:
                    if cmds.objExists(r):
                        try: cmds.rename(r, user_prefix + clean_base)
                        except: pass

                cmds.progressBar(self.prog_imp, e=True, step=1)
        finally:
            cmds.undoInfo(closeChunk=True)
            cmds.progressBar(self.prog_imp, e=True, ep=True)

    def global_fix(self, *args):
        sel = cmds.ls(sl=1)
        if len(sel)!=1: return cmds.warning("Select 1 Source Object")
        src_map, src_sgs = {}, set()
        clean = lambda n: re.sub(r'^(MI_|M_|T_|SM_)|(_\d+|\d+|_mat|_inst)$', '', n.split(':')[-1], flags=re.I).lower()
        for s in cmds.listRelatives(sel[0], s=1, f=1) or []:
            for sg in cmds.listConnections(s, type='shadingEngine') or []:
                src_sgs.add(sg)
                m = cmds.listConnections(sg+".surfaceShader")
                if m:
                    cn = clean(m[0])
                    if cn: src_map[cn] = (m[0], sg)
        cmds.undoInfo(openChunk=True)
        try:
            for sg in cmds.ls(type='shadingEngine'):
                if sg in src_sgs or 'initial' in sg: continue
                m = cmds.listConnections(sg+".surfaceShader")
                if m:
                    cn = clean(m[0])
                    if cn in src_map and m[0]!=src_map[cn][0]:
                        try: cmds.sets(cmds.sets(sg, q=1), e=1, fe=src_map[cn][1])
                        except: pass
        finally: cmds.undoInfo(closeChunk=True)

    def convert_mats(self, *args):
        typ = ['blinn','lambert','aiStandardSurface'][cmds.radioButtonGrp(self.rad_conv, q=1, sl=1)-1]
        cmds.undoInfo(openChunk=True)
        try:
            for o in cmds.ls(sl=1):
                try:
                    sg = cmds.listConnections(cmds.listRelatives(o,s=1)[0], type='shadingEngine')[0]
                    old = cmds.listConnections(sg+".surfaceShader")[0]
                    new = cmds.shadingNode(typ, asShader=1, n=old+"_"+typ)
                    c_attr = "baseColor" if typ=='aiStandardSurface' else "color"
                    src_c = "baseColor" if cmds.attributeQuery("baseColor", n=old, ex=1) else "color"
                    con = cmds.listConnections(old+"."+src_c, p=1)
                    if con: cmds.connectAttr(con[0], new+"."+c_attr, f=1)
                    cmds.connectAttr(new+".outColor", sg+".surfaceShader", f=1)
                except: pass
        finally: cmds.undoInfo(closeChunk=True)

    def break_conn(self, mode):
        attrs = {'norm':['.normalCamera'], 'rough':['.specularRoughness','.roughness'], 'metal':['.metalness','.reflectivity']}
        cmds.undoInfo(openChunk=True)
        try:
            for o in cmds.ls(sl=1):
                try:
                    sg = cmds.listConnections(cmds.listRelatives(o,s=1)[0], type='shadingEngine')[0]
                    m = cmds.listConnections(sg+".surfaceShader")[0]
                    for a in attrs.get(mode, []):
                        if cmds.connectionInfo(m+a, id=1): cmds.disconnectAttr(cmds.connectionInfo(m+a, sfd=1), m+a)
                except: pass
        finally: cmds.undoInfo(closeChunk=True)

    def bake_ao(self, *args):
        if not cmds.pluginInfo('mtoa', q=1, l=1): return cmds.warning("Arnold not loaded")
        path = cmds.textFieldButtonGrp(self.txt_bake, q=1, tx=1)
        orig = cmds.getAttr('defaultRenderGlobals.currentRenderer')
        cmds.setAttr('defaultRenderGlobals.currentRenderer', 'arnold', type='string')
        for o in cmds.ls(sl=1):
            try:
                ao = cmds.shadingNode('aiAmbientOcclusion', asShader=1); sf = cmds.shadingNode('surfaceShader', asShader=1)
                cmds.connectAttr(ao+".outColor", sf+".outColor")
                sg = cmds.sets(r=1, nss=1, em=1); cmds.sets(o, e=1, fe=sg); cmds.connectAttr(sf+".outColor", sg+".surfaceShader")
                f = os.path.join(path, o.split('|')[-1]+"_AO.png").replace("\\","/")
                cmds.convertSolidTx(sf, o, rx=2048, ry=2048, fil='png', fin=f); cmds.delete(ao, sf, sg)
            except: pass
        cmds.setAttr('defaultRenderGlobals.currentRenderer', orig, type='string')

if __name__ == "__main__": MayaPowerToolsUI()
