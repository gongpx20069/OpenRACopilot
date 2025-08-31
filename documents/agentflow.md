

```mermaid
graph TD
    A[Start: TaskClassifierAgent<br>handoffs: BuildingAgent, SquadCommanderAgent,<br>SquadFormationAgent, DefaultExecuterAgent] -->|Classify Task| B{Task Type?}
    
    B -->|base| C[BuildingAgent]
    B -->|squad_command| D[SquadCommanderAgent]
    B -->|formation| E[SquadFormationAgent]
    B -->|other| F[DefaultExecuterAgent]
    
    E -->|handoff| D
    D -->|handoff| E
    
    C -->|uses| C1[(BuildUnit)]
    C -->|uses| C2[(PlaceBuilding)]
    C -->|uses| C3[(ProduceUnits)]
    C -->|uses| C4[(DeployMCV)]
    C -->|uses| C5[(ManageProduction)]
    C -->|uses| C6[(RepairUnits)]
    C -->|uses| C7[(QueryGameState)]
    
    E -->|uses| E1[(FormGroup)]
    E -->|uses| E2[(QueryGroup)]
    E -->|uses| E3[(QueryGameState)]
    
    D -->|uses| D1[(SquadCommanderTool)]
    D -->|uses| D2[(AttackTarget)]
    D -->|uses| D3[(MoveSquadByLocation)]
    D -->|uses| D4[(StopMoveSquad)]
    D -->|uses| D5[(QueryGroup)]
    D -->|uses| D6[(SquadAttackEnemyActor)]
    D -->|uses| D7[(QueryGameState)]
    
    F -->|uses| F1[(BuildUnit)]
    F -->|uses| F2[(PlaceBuilding)]
    F -->|uses| F3[(ProduceUnits)]
    F -->|uses| F4[(DeployMCV)]
    F -->|uses| F5[(ManageProduction)]
    F -->|uses| F6[(RepairUnits)]
    F -->|uses| F7[(QueryGameState)]
    F -->|uses| F8[(MoveUnitsByLocation)]
    F -->|uses| F9[(FormGroup)]
    F -->|uses| F10[(QueryGroup)]
    F -->|uses| F11[(StopMove)]
    F -->|uses| F12[(AttackTarget)]
    
    C --> G[Execute Task]
    D --> G
    E --> G
    F --> G
    
    G --> H[End]
    ```