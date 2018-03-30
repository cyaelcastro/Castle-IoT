#!/usr/bin/pyth:
#--------------------------------------
#
#     Minecraft Python API
#        Castle Builder
#
# This script creates a castle complete
# with moat and perimeter walls.
#
# Author : Matt Hawkins
# Date   : 07/06/2014
#
# http://www.raspberrypi-spy.co.uk/
#
#---------------------------------------
#       Castle with IoT
#
# This script modifies the environment in 
# the castle, including castle properties
# working with MQTT
# 
# Author  : https://github.com/cyaelcastro
# Date    : 03/20/2018
#
# Import Minecraft libraries
import mcpi.minecraft as minecraft
import mcpi.block as block
import paho.mqtt.client as mqtt
import time

mc = minecraft.Minecraft.create()

mc.postToChat("Let's build a castle!")

#--------------------------------------
# Define Functions
#--------------------------------------

def CreateWalls(size,baseheight,height,material,battlements,walkway):
  # Create 4 walls with a specified width, height and material.
  # Battlements and walkways can also be added to the top edges.
  
  mc.setBlocks(-size,baseheight+1,-size,size,baseheight+height,-size,material) 
  mc.setBlocks(-size,baseheight+1,-size,-size,baseheight+height,size,material)
  mc.setBlocks(size,baseheight+1,size,-size,baseheight+height,size,material) 
  mc.setBlocks(size,baseheight+1,size,size,baseheight+height,-size,material) 

  # Add battlements to top edge
  if battlements==True:
    for x in range(0,(2*size)+1,2):
      mc.setBlock(size,baseheight+height+1,(x-size),material) 
      mc.setBlock(-size,baseheight+height+1,(x-size),material) 
      mc.setBlock((x-size),baseheight+height+1,size,material) 
      mc.setBlock((x-size),baseheight+height+1,-size,material)

    for x in range(0,(2*size)+1,2):
      mc.setBlock(size,baseheight+height+2,(x-size),block.TORCH) 
      mc.setBlock(-size,baseheight+height+2,(x-size),block.TORCH) 
      mc.setBlock((x-size),baseheight+height+2,size,block.TORCH) 
      mc.setBlock((x-size),baseheight+height+2,-size,block.TORCH)
      
  # Add wooden walkways
  if walkway==True:  
    mc.setBlocks(-size+1,baseheight+height-1,size-1,size-1,baseheight+height-1,size-1,block.WOOD_PLANKS)   
    mc.setBlocks(-size+1,baseheight+height-1,-size+1,size-1,baseheight+height-1,-size+1,block.WOOD_PLANKS)  
    mc.setBlocks(-size+1,baseheight+height-1,-size+1,-size+1,baseheight+height-1,size-1,block.WOOD_PLANKS)   
    mc.setBlocks(size-1,baseheight+height-1,-size+1,size-1,baseheight+height-1,size-1,block.WOOD_PLANKS)  

def CreateLandscape(moatwidth,moatdepth,islandwidth):
  # Set upper half to air
  mc.setBlocks(-128,1,-128,128,128,128,block.AIR) 
  # Set lower half of world to dirt with a layer of grass
  mc.setBlocks(-128,-1,-128,128,-128,128,block.DIRT)
  mc.setBlocks(-128,0,-128,128,0,128,block.GRASS)
  # Create water moat
  mc.setBlocks(-moatwidth,0,-moatwidth,moatwidth,-moatdepth,moatwidth,block.WATER)
  # Create island inside moat
  mc.setBlocks(-islandwidth,0,-islandwidth,islandwidth,1,islandwidth,block.GRASS)  

def CreateKeep(size,baseheight,levels):
  # Create a keep with a specified number
  # of floors levels and a roof
  height=(levels*5)+5
  
  CreateWalls(size,baseheight,height,block.STONE_BRICK,True,True)
  
  # Floors & Windows
  for level in range(1,levels+1):
    mc.setBlocks(-size+1,(level*5)+baseheight,-size+1,size-1,(level*5)+baseheight,size-1,block.WOOD_PLANKS)

  # Windows
  for level in range(0,levels+1):
    CreateWindows(0,(level*5)+baseheight+2,size,"N")
    CreateWindows(0,(level*5)+baseheight+2,-size,"S")
    CreateWindows(-size,(level*5)+baseheight+2,0,"W")
    CreateWindows(size,(level*5)+baseheight+2,0,"E")

  # Door
  mc.setBlocks(0,baseheight+1,size,0,baseheight+2,size,block.AIR)

def CreateWindows(x,y,z,dir):

  if dir=="N" or dir=="S":
    z1=z
    z2=z
    x1=x-2
    x2=x+2

  if dir=="E" or dir=="W":
    z1=z-2
    z2=z+2
    x1=x
    x2=x

  mc.setBlocks(x1,y,z1,x1,y+1,z1,block.AIR)
  mc.setBlocks(x2,y,z2,x2,y+1,z2,block.AIR) 

  if dir=="N":
    a=3
  if dir=="S":
    a=2
  if dir=="W":
    a=0
  if dir=="E":
    a=1

  mc.setBlock(x1,y-1,z1,109,a)
  mc.setBlock(x2,y-1,z2,109,a)
  
def dayLight(light):
  if light:
    mc.setBlocks(-50,60,-60,50,60,60,0)
  else:
    mc.setBlocks(-50,60,-60,50,60,60,1)

def lightFloor(level, light):
  #for i in range(1,level+1):
  if light:
    mc.setBlocks(-4,5*(level+1),-4,4,5*(level+1),4,51)
  else:
    mc.setBlocks(-4,5*(level+1),-4,4,5*(level+1),4,block.AIR)


#--------------------------------------
#
# MQTT
#
#--------------------------------------

daylightFlag = True
outterWallFlag = True
gateFlag = False
outterWallHeight = 8 
innerWallHeight = 8
level0LightFlag = False
level1LightFlag = False
level2LightFlag = False
level3LightFlag = False


def on_message(client, userdata, message):
  global daylightFlag, outterWallHeight, innerWallHeight, outterWallFlag, gateFlag, level0LightFlag, level1LightFlag, level2LightFlag, level3LightFlag
  if message.topic == "/mc/nodeRed/Daylight":
    if message.payload.decode("utf-8") == "Light" and daylightFlag:
      dayLight(True)
      daylightFlag = False
    if message.payload.decode("utf-8") == "No light" and not daylightFlag:
      dayLight(False)
      daylightFlag = True

  if message.topic == "/mc/nodeRed/CastleGate":
    if message.payload.decode("utf-8") == "Open" and outterWallFlag:
      gateFlag = True
      OutterWall(outterWallHeight,gateFlag)
      InnerWall(innerWallHeight,gateFlag)
      outterWallFlag = False
      
    if message.payload.decode("utf-8") == "Close" and not outterWallFlag:
      gateFlag = False
      OutterWall(outterWallHeight,gateFlag)
      InnerWall(innerWallHeight,gateFlag)
      outterWallFlag = True
    
  if message.topic == "/mc/nodeRed/CastleLight/0":
    if message.payload.decode("utf-8") == "On" and level0LightFlag:
      lightFloor(0,True)
      level0LightFlag = False
    if message.payload.decode("utf-8") == "Off" and not level0LightFlag:
      lightFloor(0,False)
      level0LightFlag = True

  if message.topic == "/mc/nodeRed/CastleLight/1":
    if message.payload.decode("utf-8") == "On" and level1LightFlag:
      lightFloor(1,True)
      level1LightFlag = False
    if message.payload.decode("utf-8") == "Off" and not level1LightFlag:
      lightFloor(1,False)
      level1LightFlag = True

  if message.topic == "/mc/nodeRed/CastleLight/2":
    if message.payload.decode("utf-8") == "On" and level2LightFlag:
      lightFloor(2,True)
      level2LightFlag = False
    if message.payload.decode("utf-8") == "Off" and not level2LightFlag:
      lightFloor(2,False)
      level2LightFlag = True

  if message.topic == "/mc/nodeRed/CastleLight/3":
    if message.payload.decode("utf-8") == "On" and level3LightFlag:
      lightFloor(3,True)
      level3LightFlag = False
    if message.payload.decode("utf-8") == "Off" and not level3LightFlag:
      lightFloor(3,False)
      level3LightFlag = True

  if message.topic == "/mc/nodeRed/InnerWalls":
    innerWallHeight = int(message.payload.decode("utf-8"))
    InnerWall(innerWallHeight,gateFlag)

  if message.topic == "/mc/nodeRed/OutterWalls":
    outterWallHeight = int(message.payload.decode("utf-8"))
    OutterWall(outterWallHeight,gateFlag)

def OutterWall (height, openGate):
  
  CreateWalls(20,1,50,block.AIR,False,False)
  CreateWalls(21,1,52,block.AIR,False,False)
  CreateWalls(21,1,height,block.STONE_BRICK,True,True)
  mc.setBlocks(-2,2,21,2,6,21,block.AIR)
  if openGate:
    #print "Open gate"
    mc.setBlocks(-2,2,21,2,6,21,block.AIR)
    mc.setBlocks(-2,1,24,2,1,34,block.WOOD_PLANKS)
  else:
    mc.setBlocks(-2,1,24,2,1,34,block.AIR)
    mc.setBlocks(-2,2,21,2,6,21,block.WOOD_PLANKS)
  

def InnerWall (height, openGate):
  CreateWalls(13,1,52,block.AIR,False,False)
  CreateWalls(12,1,50,block.AIR,False,False)
  CreateWalls(13,1,height,block.STONE_BRICK,True,True)
  mc.setBlocks(-1,2,13,1,4,13,block.WOOD_PLANKS)
  if openGate:
    mc.setBlocks(-1,2,13,1,4,13,block.AIR)

if __name__ == '__main__':

  #broker = "192.168.1.118"
  broker = "iot.eclipse.org"
  client = mqtt.Client("RaspberryCastle")
  client.on_message = on_message
  client.connect(broker)

 # print("Create ground and moat")
  CreateLandscape(33,10,23)  

  print("Create outer walls")
#  CreateWalls(21,1,8,block.STONE_BRICK,True,True)
  global outterWallHeight, gateFlag, innerWallHeight
  OutterWall(outterWallHeight,gateFlag)

  #print("Create inner walls")
  InnerWall(innerWallHeight,gateFlag)
  

  #print("Create Keep with 4 levels")
  CreateKeep(5,1,4)

  #print("Position player on Keep's walkway")
  mc.player.setPos(0,30,4)
  #lightFloor(4,True)

  

  while True:
    client.loop_start()
    client.subscribe([("/mc/nodeRed/Daylight",0),("/mc/nodeRed/CastleGate",0),("/mc/nodeRed/CastleLight/#",0),("/mc/nodeRed/OutterWalls",0),("/mc/nodeRed/InnerWalls",0)])
    time.sleep(3) # wait
    client.loop_stop() #stop the loop