from math import pi, sin, cos
from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile
from panda3d.core import DirectionalLight, AmbientLight, BitMask32, TextNode
from panda3d.core import TransparencyAttrib
from panda3d.core import WindowProperties
from panda3d.core import CollisionTraverser, CollisionNode, CollisionBox, CollisionRay, CollisionHandlerQueue, CollisionHandlerPusher, CollisionSphere
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import ClockObject

loadPrcFile('settings.prc')

def degToRad(degrees):
    return degrees * (pi / 180.0)

class MyGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.hotbarSlots = ['grass', 'dirt', 'sand', 'stone', 'wood']
        self.playerBuilt = set()
        self.pusher = CollisionHandlerPusher()
        self.selectedBlockType = 'grass'
        self.globalClock = ClockObject.getGlobalClock
        self.loadModels()
        self.setupLights()
        self.generateChunk()
        self.setFrameRateMeter(True)
        self.camera.setPos(-10, 16, 16) 
        self.setupCamera()
        self.captureMouse()
        self.setupControls()
        self.setupInventoryUI()
        self.taskMgr.add(self.update, 'update')
        self.globalClock = ClockObject.getGlobalClock()
        self.customFont = self.loader.loadFont('Minecraft.ttf')
        self.blockText = OnscreenText(
            text="Grass", 
            pos=(0, -0.75),                  
            scale=0.07,                        
            fg=(1, 1, 1, 1),
            shadow=(0, 0, 0, 0.8),
            font=self.customFont,                            
            align=TextNode.ACenter,                            
            mayChange=True
        )
        self.render.setTwoSided(False)
    
    def update(self, task):
        
        dt = self.globalClock.getDt()
        playerMoveSpeed = 5

        x_movement = 0
        y_movement = 0
        
        z_movement = 0
    
        if self.keyMap['forward']:
            x_movement -= dt * playerMoveSpeed * sin(degToRad(self.camera.getH()))
            y_movement += dt * playerMoveSpeed * cos(degToRad(self.camera.getH()))
        if self.keyMap['backward']:
            x_movement += dt * playerMoveSpeed * sin(degToRad(self.camera.getH()))
            y_movement -= dt * playerMoveSpeed * cos(degToRad(self.camera.getH()))
        if self.keyMap['left']:
            x_movement -= dt * playerMoveSpeed * cos(degToRad(self.camera.getH()))
            y_movement -= dt * playerMoveSpeed * sin(degToRad(self.camera.getH()))
        if self.keyMap['right']:
            x_movement += dt * playerMoveSpeed * cos(degToRad(self.camera.getH()))
            y_movement += dt * playerMoveSpeed * sin(degToRad(self.camera.getH()))
        if self.keyMap['up']:
            z_movement += dt * playerMoveSpeed
        if self.keyMap['down']:
            z_movement -= dt * playerMoveSpeed    
        
        self.camera.setPos(
            self.camera.getX() + x_movement,
            self.camera.getY() + y_movement,
            self.camera.getZ() + z_movement
        )
        
        if self.cameraSwingActivated:
            md = self.win.getPointer(0)
            mouseX = md.getX()
            mouseY = md.getY()

            mouseChangeX = mouseX - self.lastMouseX
            mouseChangeY = mouseY - self.lastMouseY

            self.cameraSwingFactor = 10
            currentH = self.camera.getH()
            currentP = self.camera.getP()

            self.camera.setHpr(
                currentH - mouseChangeX * dt * self.cameraSwingFactor,
                min(90, max(-90, currentP - mouseChangeY * dt * self.cameraSwingFactor)),
                0
            )

            self.lastMouseX = mouseX
            self.lastMouseY = mouseY
        
        return task.cont

    def setSelectedBlockType(self, type):
        self.selectedBlockType = type
        self.blockText.setText(f"{type.capitalize()}")
    
    def handleLeftClick(self):
        self.captureMouse()
        self.removeBlock()

    def setupInventoryUI(self):
        self.hotbarBg = OnscreenImage(image='Hotbar.png',
                                      pos= (0, 0, -0.85),
                                      scale=(0.6, 1, 0.08))
        self.hotbarBg.setTransparency(TransparencyAttrib.MAlpha)
        self.selector_ui = OnscreenImage(image='Hotbar_selector.png',
                                         pos=(-0.5241, 0, -0.85),
                                         scale=(0.08, 1, 0.08))
        self.selector_ui.setTransparency(TransparencyAttrib.MAlpha)

    def selectSlot(self, slotIndex):
        newXPos = -0.5241 + (slotIndex * 0.13)
        self.selector_ui.setX(newXPos)
        self.current_block_type = self.hotbarSlots[slotIndex]

    def removeBlock(self):
        self.cTrav.traverse(self.render) 

        if self.rayQueue.getNumEntries() > 0:
            self.rayQueue.sortEntries()
            rayHit = self.rayQueue.getEntry(0)
            
            hitCollider = rayHit.getIntoNodePath()
            hitObject = hitCollider.getPythonTag('owner') 
            
            if hitObject:
                distanceFromPlayer = hitObject.getDistance(self.camera)
                if distanceFromPlayer < 40: 
                    hitCollider.clearPythonTag('owner')
                    hitObject.removeNode()
                    hitCollider.removeNode()

    def placeBlock(self):
        self.cTrav.traverse(self.render)

        if self.rayQueue.getNumEntries() > 0:
            self.rayQueue.sortEntries()
            rayHit = self.rayQueue.getEntry(0)
            
            hitCollider = rayHit.getIntoNodePath()
            normal = rayHit.getSurfaceNormal(self.render) 
            hitObject = hitCollider.getPythonTag('owner')

            if hitObject:
                distanceFromPlayer = hitObject.getDistance(self.camera)
                if distanceFromPlayer < 40:
                    hitBlockPos = hitObject.getPos()
                    newBlockPos = hitBlockPos + normal * 2 
                    self.createNewBlock(newBlockPos.x, newBlockPos.y, newBlockPos.z, self.selectedBlockType)
    
    def updateKeyMap(self, key, value):
        self.keyMap[key] = value

    def setupControls(self):
        self.keyMap = {
            "forward": False,
            "backward": False,
            "left": False,
            "right": False,
            "up": False,
            "down": False,

        }

        self.accept('escape', self.releaseMouse)
        self.accept('mouse1', self.handleLeftClick)
        self.accept('mouse3', self.placeBlock)

        self.accept('w', self.updateKeyMap, ['forward', True])
        self.accept('w-up', self.updateKeyMap, ['forward', False])
        self.accept('a', self.updateKeyMap, ['left', True])
        self.accept('a-up', self.updateKeyMap, ['left', False])
        self.accept('s', self.updateKeyMap, ['backward', True])
        self.accept('s-up', self.updateKeyMap, ['backward', False])
        self.accept('d', self.updateKeyMap, ['right', True])
        self.accept('d-up', self.updateKeyMap, ['right', False])
        self.accept('space', self.updateKeyMap, ['up', True])
        self.accept('space-up', self.updateKeyMap, ['up', False])
        self.accept('lshift', self.updateKeyMap, ['down', True])
        self.accept('lshift-up', self.updateKeyMap, ['down', False])

        self.accept('1', self.setSelectedBlockType, ['grass'])
        self.accept('2', self.setSelectedBlockType, ['dirt'])
        self.accept('3', self.setSelectedBlockType, ['sand'])
        self.accept('4', self.setSelectedBlockType, ['stone'])
        self.accept('5', self.setSelectedBlockType, ['wood'])
        self.accept('1', self.selectSlot, [0])
        self.accept('2', self.selectSlot, [1])
        self.accept('3', self.selectSlot, [2])
        self.accept('4', self.selectSlot, [3])
        self.accept('5', self.selectSlot, [4])
        self.accept('6', self.selectSlot, [5])
        self.accept('7', self.selectSlot, [6])
        self.accept('8', self.selectSlot, [7])
        self.accept('9', self.selectSlot, [8])

    def captureMouse(self):
        self.cameraSwingActivated = True
        md = self.win.getPointer(0)
        self.lastMouseX = md.getX()
        self.lastMouseY = md.getY()

        properties = WindowProperties()
        properties.setCursorHidden(True)
        properties.setMouseMode(WindowProperties.M_relative)
        self.win.requestProperties(properties)

    def releaseMouse(self):
        self.cameraSwingActivated = False
        properties = WindowProperties()
        properties.setCursorHidden(False)
        properties.setMouseMode(WindowProperties.M_absolute)
        self.win.requestProperties(properties)

    def setupCamera(self):
        self.disableMouse()
        self.camLens.setFov(80)
        self.camLens.setNear(0.1)
        self.camLens.setFar(100)

        crosshairs = OnscreenImage(
            image = 'crosshairs.png',
            pos = (0, 0, 0),
            scale = 0.05,
        )
        crosshairs.setTransparency(TransparencyAttrib.MAlpha)

        playerSphere = CollisionSphere(0, 0, 0, 1.2)
        playerNode = CollisionNode('player-collider')
        playerNode.addSolid(playerSphere)
        playerNode.setFromCollideMask(BitMask32.bit(1))
        playerNode.setIntoCollideMask(0)
        playerNodePath = self.camera.attachNewNode(playerNode)
        self.pusher.addCollider(playerNodePath, self.camera)

        self.cTrav = CollisionTraverser()
        self.cTrav.addCollider(playerNodePath, self.pusher)
        
        ray = CollisionRay()
        ray.setFromLens(self.camNode, (0, 0))
        rayNode = CollisionNode('line-of-sight')
        rayNode.addSolid(ray)
        rayNode.setFromCollideMask(BitMask32.bit(2)) 
        rayNode.setIntoCollideMask(0)
        
        rayNodePath = self.camera.attachNewNode(rayNode)
        self.rayQueue = CollisionHandlerQueue()
        self.cTrav.addCollider(rayNodePath, self.rayQueue)

    def generateChunk(self):
        self.world_data = {}
        for z in range(15):
            for x in range(16):
                for y in range(16):
                    self.world_data[(x, y, z)] = 'grass' if z == 0 else 'dirt' if z <= 4 else 'stone'
        self.z = z
        self.x = x
        self.y = y

        for (x, y, z), block_type in self.world_data.items():
            self.createNewBlock(x * 2 - 16, y * 2 - 16, -z * 2, block_type, needsCollision=True)
            
        
    def createNewBlock(self, x, y, z, type, needsCollision = True):
        self.newBlockNode = self.render.attachNewNode('new-block-placeholder')
        self.newBlockNode.setPos(x, y, z)

        if type == 'grass':
            self.grassBlock.instanceTo(self.newBlockNode)
        elif type == 'dirt':
            self.dirtBlock.instanceTo(self.newBlockNode)
        elif type == 'sand':
            self.sandBlock.instanceTo(self.newBlockNode)
        elif type == 'stone':
            self.stoneBlock.instanceTo(self.newBlockNode)
        elif type == 'wood':
            self.woodLog.instanceTo(self.newBlockNode)

        # CONFIGURACIÓN CORREGIDA: Ajustamos el centro de la caja a la posición del bloque
        self.blockSolid = CollisionBox((x, y, z), 1, 1, 1)
        self.blockNode = CollisionNode('block-collision-node')
        self.blockNode.addSolid(self.blockSolid)
        self.blockNode.setIntoCollideMask(BitMask32.bit(1) | BitMask32.bit(2)) 
        
        # Adjuntamos el colisionador directamente al render para independizar las coordenadas globales
        collider = self.render.attachNewNode(self.blockNode)
        collider.setPythonTag('owner', self.newBlockNode)

    def loadModels(self):
        self.grassBlock = self.loader.loadModel('grass-block.glb')
        self.dirtBlock = self.loader.loadModel('dirt-block.glb')
        self.stoneBlock = self.loader.loadModel('stone-block.glb')
        self.sandBlock = self.loader.loadModel('sand-block.glb')
        self.woodLog = self.loader.loadModel('oak-log.glb')

    def setupLights(self):
        mainLight = DirectionalLight('main light')
        mainLightNodePath = self.render.attachNewNode(mainLight)
        mainLightNodePath.setHpr(30, -60, 0)
        self.render.setLight(mainLightNodePath)

        ambientLight = AmbientLight('ambient light')
        ambientLight.setColor((0.3, 0.3, 0.3, 1))
        ambientLightNodePath = self.render.attachNewNode(ambientLight)
        self.render.setLight(ambientLightNodePath)

game = MyGame()
game.run()