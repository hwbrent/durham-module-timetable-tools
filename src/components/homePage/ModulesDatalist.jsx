import React, { useState, useEffect } from 'react';

const {
    REACT_APP_HOMEPAGE,
    REACT_APP_SERVER_URL
} = process.env;

/**
 * Renders a <datalist> and accompanying 
 * @returns a React Component
 */
 function ModulesDatalist(props) {

    // `modules` is the list of full module names
    const [ modules, setModules ] = useState([]);

    useEffect(
        () => {
            // fetches the full names of the modules (e.g. "ACCT0001 - Accounting Placement Bootcamp (L1)")
            async function effect() {
                try {
                    const response = await fetch(`${REACT_APP_SERVER_URL}/get-module-names`,{
                        method: "GET",
                        headers: {"Content-Type": "application/json"}
                    });
                    const data = await response.json();
                    setModules(data);
                } catch (error) {
                    alert(error);
                }
            }
            effect();
        },
        [] // only executes in first render
    );

    const form = (
        <form onSubmit={(event) => props.handleFormSubmit(event, modules)}>
            <label>
                Select your desired modules:
                <input type="text" list="modulesDatalist" size="50" placeholder="Click on the arrow or begin typing"/>
            </label>
            <datalist id="modulesDatalist">
                {modules.map((value, index) => <option key={index} value={value} />)}
            </datalist>
            <input type="submit" />
        </form>
    );

    return form;
}

export default ModulesDatalist;
