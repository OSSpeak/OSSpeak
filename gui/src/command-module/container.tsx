import React from 'react';
import ReactDOM from 'react-dom';
import { wsFetch } from '../websocket';
import CommandModulePanel from './panel';
import CommandModuleTabs from './tabs';
import CommandModuleList from './list/list';
import { isEqual } from 'lodash';
import { CommandModuleContainerProps, CommandModuleContainerState } from "./types";

class CommandModuleContainer extends React.Component<CommandModuleContainerProps, CommandModuleContainerState> {

    state: CommandModuleContainerState = {
        selectedPath: null,
        activePaths: [],
    }

    constructor(props: any) {
        super(props);
        this.state.selectedPath
    }

    get nestedPaths() {
        return Object.keys(this.props.recognitionIndex.commandModules);
    }

    onListItemClick = (clickedPath: string) => {
        // const updatedState: Partial<CommandModuleContainerState> = { selectedPath: clickedPath }
        const updatedState: any = { selectedPath: clickedPath }
        const pathOpen = this.state.activePaths.includes(clickedPath);
        if (!pathOpen) updatedState.activePaths = this.state.activePaths.concat([clickedPath])
        this.setState(updatedState);
    }


    componentDidMount() {

    }

    render() {
        const cmdModules = this.props.recognitionIndex.commandModules;
        const module = this.state.selectedPath === null ? null : cmdModules[this.state.selectedPath]
        return (
            <div id="cm-container">
                <CommandModuleList onListItemClick={this.onListItemClick} paths={this.nestedPaths} />
                {this.state.selectedPath && (
                    <div id="command-module-contents">
                        <CommandModuleTabs paths={this.state.activePaths} />
                        {<CommandModulePanel module={module} />}
                    </div>
                )}
                {this.state.activePaths}
            </div>
        );
    }
}

export default CommandModuleContainer;