import json
import os

# Directory where json file is searched for
# Default: DEFAULT
CHECK_FILE_PATH = r"DEFAULT"
# Outfile encoding, make sure to add it!!
# Default: [.json, .csv]
OUTTYPE = ".json"
JSON_ACCUMULATOR = {
  'meta' : {},
  'replay' : []
}

PLAYERS = []
CURRENT_TEAM = 0
CURRENT_PLAYER_NAME = None
CURRENT_SELECTED_UNIT = None
CURRENT_MAP_NAME = None
PREVIOUS_ACTION = None
SPAWNED_UNIT_PACKAGE = None
PREV_FRAME_DATA = None

CURRENT_FIELD_UNITS = []
  
RACE_LOOKUP_TABLE = {
  1 : "soldier",
  2 : "runner",
  3 : "heavy",
  4 : "sniper",
  5 : "medic",
  6 : "scrambler",
  7 : "unknownUnit"
}


def main():
  json_file = getMostRecentJsonFilePath()

  decoded_json = {}
  
  with open(json_file, "r") as file:
    buffer = file.read()
    decoded_json = json.loads(buffer)
    decoded_json = decoded_json['viewResponse']
    
  
  game_state = json.loads(decoded_json['gameState'])
  game_state = game_state['gameState']
  
  game_over_data = game_state['gameOverData']
  game_replay = game_state['replay']
  
  game_id = decoded_json['room']
  map_name = game_state['mapName']
  game_type = len(game_over_data['winners'])


  per_turn_data = []
  csv_out_string = ""
  
  frame_number = 0

  if OUTTYPE == ".csv":
      csv_out_string += (f"Game ID,{game_id}\n")
      csv_out_string += (f"Map Name,{map_name}\n")
      csv_out_string += (f"Game Type,{game_type}\n")
      csv_out_string += (f"Players: ")
      csv_out_string += (", ".join(PLAYERS))
      csv_out_string += ("\n\n")
      csv_out_string += ('player,turn,frame,description,action,unit,id,origin,dest\n')
      
  elif OUTTYPE == ".json":
    JSON_ACCUMULATOR['meta'].update({
      'gameID' : game_id,
      'mapName': map_name,
      'gameType': game_type,
      'players': PLAYERS
    })
      
  # Preprocess
  for action in game_replay:
    # per_turn_data.append(parseTurnList(action))
    pre_action = parseTurnList(action)
    pre_action.update({'frameNumber': str(frame_number)})
    per_turn_data.append(pre_action)
    frame_number += 1
    

  # Writer
  turn_number = 0
  for turn_object in per_turn_data:
    
    # Not actually allowed to be None >:(
    desctiption = None
    
    action = None
    unit   = None
    id     = None
    origin = None
    dest   = None
    
    descriptByPass = False

    match turn_object['packageType']:
      case 'state':
        descriptByPass = True
        pass
      case 'selectSpawn':
        descriptByPass = True
        pass
      case 'eat':
        descriptByPass = True
        pass
      case 'rangedAttack':
        obData = turn_object['package']['data']
        if 'error' not in obData:
          unit =  obData['unitName']
          id = obData['unitID']
          dest = f"i:{obData['toi']};j:{obData['toj']}"
          desctiption = f"Player {turn_object['package']['player']} used ranged attack on tile {dest}" 
        else:
          desctiption = f"Ranged Attack Parsing error"
        
      case 'start':
        desctiption = f"Player {turn_object['package']['player']} started turn"

      case 'end':
        desctiption = f"Player: {turn_object['package']['player']} ended turn"
        turn_number += 1

      case 'heal':
        desctiption = f"Player {turn_object['package']['player']} healed"

      case 'spit':
        desctiption = f"Player {turn_object['package']['player']} spit"
      case 'spawnUnit':
        descriptByPass = True
        pass
      case 'selectedUnit':
        desctiption = f"Selected Unit: {turn_object['package']['data']['unitID']}"
        unit =  turn_object['package']['data']['unitName']
        id = turn_object['package']['data']['unitID']
      case 'move':
        if 'error' not in turn_object['package']['data']:
          obData = turn_object['package']['data']
          desctiption = f"{obData['unitName']} with ID: {obData['unitID']} moved from i:{obData['fromi']};j:{obData['fromj']} to i:{obData['toi']};j:{obData['toj']}"
          unit =  turn_object['package']['data']['unitName']
          id = turn_object['package']['data']['unitID']
          origin = f"i:{obData['fromi']};j:{obData['fromj']}"
          dest = f"i:{obData['toi']};j:{obData['toj']}"
        else:
          desctiption = "Movement Parsing Error"


      case _:
        print("unknown action found")
        raise Exception("Unknown package type")

    if OUTTYPE == ".csv" and not descriptByPass:
      if desctiption != None:
        csv_out_string += (turn_object['package']['player'])
        csv_out_string += (", ")
        
        csv_out_string += (str(turn_number))
        csv_out_string += (", ")

        csv_out_string += (turn_object['frameNumber'])
        csv_out_string += (", ")

        csv_out_string += (desctiption)
        csv_out_string += (", ")
        
        csv_out_string += (turn_object['packageType'])
        csv_out_string += (", ")
        
        csv_out_string += ("" if unit == [] or unit == None else unit[0])
        csv_out_string += (", ")
        
        csv_out_string += ("" if id == None else id)
        csv_out_string += (", ")
        
        csv_out_string += ("" if origin == None else origin)
        csv_out_string += (", ")
        
        csv_out_string += ("" if dest == None else dest)
        csv_out_string += ("\n")
        
      else:
        if not descriptByPass:
          print(f"Current frame: {turn_object['packageType']}")
          raise Exception("Missing description")
            
    elif OUTTYPE == ".json" and not descriptByPass:
      JSON_ACCUMULATOR['replay'].append(
        {
          'player': turn_object['package']['player'],
          'turnNumber': str(turn_number),
          'frameNumber': turn_object['frameNumber'],
          'description': desctiption,
          'action': turn_object['packageType'],
          'unit': "" if unit == [] or unit == None else unit[0],
          'id': "" if id == None else id,
          'origin': "" if origin == None else origin,
          'dest': "" if dest == None else dest,
        }
      )
      
      
    else:
      if not descriptByPass:
        print("Did you forget to add a file type handler?")
        raise Exception("Unknown file type for OUTTYPE")
    
  pass
      
  if OUTTYPE == ".json":
    with open("output.json", "w") as file:
      file.write(json.dumps(JSON_ACCUMULATOR, indent=2))
  elif OUTTYPE == ".csv":
    with open("output.csv", "w") as file:
      file.write(csv_out_string)
      
def parseTurnList(replayList):
  global RACE_LOOKUP_TABLE, CURRENT_SELECTED_UNIT, CURRENT_FIELD_UNITS
  global CURRENT_TEAM, CURRENT_MAP_NAME, CURRENT_PLAYER_NAME, PREVIOUS_ACTION
  global SPAWNED_UNIT_PACKAGE, PREV_FRAME_DATA, PLAYERS, JSON_ACCUMULATOR
  
  
  frame_data   = None
  action       = None
  pawn_move_package = None
  pawn_select_package = None

  current_game_state = json.loads(replayList['frameData'])
  frame_name = replayList['frameName']

  match frame_name:
    case 'StartTurnAction':
      action = 'start'
      CURRENT_TEAM = 1 if CURRENT_TEAM == 0 else 0
      
      
    case 'EndTurnAction':
      action = "end"
    
    case 'SelectUnitAction':
      action = 'selectedUnit'
      frame_data = json.loads(replayList['frameData'])['action']

      if PREVIOUS_ACTION == 'spawnUnit':
        max_id = max([item['id'] for item in CURRENT_FIELD_UNITS ])
        SPAWNED_UNIT_PACKAGE.update({
          'i' : int((frame_data['touchX'])),
          'j' : int(frame_data['touchY']),
          'owner': CURRENT_PLAYER_NAME,
          'id': max_id+1
        })
        CURRENT_FIELD_UNITS.append(SPAWNED_UNIT_PACKAGE)
      
      unit_id = frame_data['pawnID']
      unit_name = [unit['unitName'] for unit in CURRENT_FIELD_UNITS if unit['id'] == unit_id]
      
      pawn_select_package = {
          'unitName': unit_name,
          'unitID' : str(unit_id),
      }
      pass
      
      
    case 'MoveUnitAction':
      action = 'move'
      frame_data = json.loads(replayList['frameData'])['action']
      unit_id = frame_data['pawnID']

      try:
        old_unit_object = [unit for unit in CURRENT_FIELD_UNITS if unit['id'] == unit_id][0]
        pawn_move_package = {
            'unitName': str(old_unit_object['unitName']),
            'unitID': str(old_unit_object['id']),
            'toi': frame_data['desti'] ,
            'toj': frame_data['destj'] ,
            'fromi' : old_unit_object['i'],
            'fromj'   : old_unit_object['j'],
          }
      except:
        pawn_move_package = {'error' : True}
      
      
    case 'RangeAttackAction':
      action = 'rangedAttack'
      frame_data = json.loads(replayList['frameData'])['action']
      unit_id = frame_data['pawnID']

      try:
        old_unit_object = [unit for unit in CURRENT_FIELD_UNITS if unit['id'] == unit_id][0]
        frame_data = json.loads(replayList['frameData'])['action']
        pawn_move_package = {
            'unitName': str(old_unit_object['unitName']),
            'unitID': str(old_unit_object['id']),
            'toi': frame_data['desti'] ,
            'toj': frame_data['destj'] ,
            'fromi'   : None,
            'fromj'   : None,
          }
      
      except:
        pawn_move_package = {
          'error' : True
        }  

      
    case 'SpawnUnitAction':
      action = "spawnUnit"
      # Not normal case, does not provide unit id on spawn
      # Unit id is given on select???
      
      frame_data = json.loads(replayList['frameData'])
      PREV_FRAME_DATA = frame_data
      SPAWNED_UNIT_PACKAGE = {
          "unitName": RACE_LOOKUP_TABLE[frame_data['action']['role']],
      }

      pass
      
    case 'EatAction':
      action = 'eat'
      pass
    case 'SpitAction':
      action = 'spit'
      pass
    case 'State':
      action = 'state'
      
      # Crazy 
      CURRENT_PLAYER_NAME = current_game_state['gameState']['settings'][current_game_state['gameState']['currentPlayer']]['name']
      if CURRENT_PLAYER_NAME not in PLAYERS:
        PLAYERS.append(CURRENT_PLAYER_NAME)
        
      game_state = json.loads(replayList['frameData'])['gameState']
      setBoardState(game_state)
      pass
      
    case "SelectSpawnTileAction":
      action = 'selectSpawn'
      pass
    case "ActiveHealAction":
      action = 'heal'
      pass
    case _:
      print("found new action")
      print(frame_name)
      input("Figure out the new action from context and change it in the fileotherwise live without it")
    
       

  PREVIOUS_ACTION = action
  pre_pack = {
    'packageType' : action,
    'package' : {
      'player': CURRENT_PLAYER_NAME,
      'action': action,
    }
  }
  
  if action != 'selectedUnit' or action != 'move':
    if pawn_move_package != None:
      pre_pack['package'].update({'data': pawn_move_package})
    elif pawn_select_package != None :
      pre_pack['package'].update({'data': pawn_select_package})
  else:
    print("Crazy new package has appeared in the package updater")
    raise Exception("Unknown update package")
  
  return pre_pack

def setBoardState(state_frame):
  global CURRENT_FIELD_UNITS, RACE_LOOKUP_TABLE
  
  CURRENT_FIELD_UNITS = []

  for i in state_frame['units']:
    CURRENT_FIELD_UNITS.append({
      "unitName": RACE_LOOKUP_TABLE[i['race']],
      "i" : i['positionJ'],
      "j" : i['positionI'],
      "owner" : i['owner'],
      "id" : i['identifier']
    })
    
    pass

def getMostRecentJsonFilePath():
  global CHECK_FILE_PATH
  search_path = CHECK_FILE_PATH

  if CHECK_FILE_PATH == "DEFAULT":
    search_path = os.path.join(os.path.expanduser("~"), "downloads")

  for r, d, files in os.walk(search_path):
    for file in files:
      if file.endswith(".json"):
        return str(r +  "/" + file);
  
  raise Exception(f"Could not find json file in download path")
      

main()
    
