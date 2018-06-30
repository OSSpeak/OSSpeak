export interface CommandModule {
    id: string
    commands: Command[]
}
export interface Command {
    rule: Rule
    action: Action
}

export interface Rule {
    text: string
}
export interface Action {
    pieces: ActionPiece[]
}
export interface ActionPiece {
    type: 'dsl'
}

export interface RecognitionIndex {
    commandModules: { [path: string]: CommandModule },
    osSep: string
}
