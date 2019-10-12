#Fusion360 Python
#Author-kantoku
#Description-ボディを複数の面で分割するサンプル

import adsk.core, adsk.fusion, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        des = adsk.fusion.Design.cast(app.activeProduct)
        root = des.rootComponent

        #ターゲット
        target = root.bRepBodies.item(0)

        #ツール
        surfs = adsk.core.ObjectCollection.create()
        surfs.add(root.bRepBodies.item(1))
        surfs.add(root.bRepBodies.item(2))

        #ツールから厚み(対称的)
        thickenValue = adsk.core.ValueInput.createByReal(0.01) #厚み
        thickenFeatures = root.features.thickenFeatures
        thickenInput = thickenFeatures.createInput(surfs, thickenValue, True,  adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        thickenFeature = thickenFeatures.add(thickenInput)
        thicks = adsk.core.ObjectCollection.create()
        for t in thickenFeature.bodies:
            thicks.add(t)

        #ターゲットコピペ
        copy_target = root.features.copyPasteBodies.add(target).bodies.item(0)

        #ターゲットと厚みで差
        combInput = root.features.combineFeatures.createInput(target,thicks)
        combInput.isKeepToolBodies = True
        combInput.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
        cutBodies = root.features.combineFeatures.add(combInput).bodies

        #ターゲットと厚みで積
        combInput = root.features.combineFeatures.createInput(copy_target,thicks)
        combInput.isKeepToolBodies = False
        combInput.operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
        interBodies = root.features.combineFeatures.add(combInput).bodies

        #厚みをツールで分割
        splits = adsk.core.ObjectCollection.create()
        splitBodyFeats = root.features.splitBodyFeatures
        for idx in range(interBodies.count):
            splitBodyInput = splitBodyFeats.createInput(interBodies.item(idx), surfs.item(idx), False)
            splitBodies = splitBodyFeats.add(splitBodyInput).bodies
            _ = [splits.add(b) for b in splitBodies]

        #組み合わせる
        combs = GroupByBody(cutBodies,splits)
        for comb in combs:
            tgt = comb[0]
            tools = adsk.core.ObjectCollection.create()
            for bdy in comb[1:]:
                tools.add(bdy)
            #和
            combInput = root.features.combineFeatures.createInput(tgt,tools)
            combInput.isKeepToolBodies = False
            combInput.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            root.features.combineFeatures.add(combInput)

        ui.messageBox('done')
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

#組み合わせを探る
def GroupByBody(targets, splits):
    app = adsk.core.Application.get()
    ui = app.userInterface
    combs = []
    for tgt in targets:
        lst = [tgt]
        for slt in splits:
            if hasSurfMatch(tgt, slt):
                lst.append(slt)
        if len(lst) > 1:
            combs.append(lst)
    return combs

#Body同士で一致面がある？
def hasSurfMatch(bodyA, bodyB):
    for fa in bodyA.faces:
        for fb in bodyB.faces:
            if IsSurfMatch(fa, fb):
                return True
    return False

#Faceが一致？
def IsSurfMatch(surfA, surfB):
    tol = 0.1 #面積一致トレランス
    if surfA.centroid.isEqualTo(surfB.centroid):
        if abs(surfA.area - surfB.area) < tol:
            return True
    return False
