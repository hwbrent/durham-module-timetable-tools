import React, { useState, useEffect } from 'react';
import handleFetch from '../functions/handleFetch';

/**
 * Renders a <datalist> and accompanying 
 * @returns a React Component
 */
 function ModulesDatalist(props) {

    // `modules` is the list of full module names
    const [ modules, setModules ] = useState([]);

    // in the first render, fetches the full names of the modules (not just the codes, e.g. "ACCT0001 - Accounting Placement Bootcamp (L1)")
    useEffect(() => {
        async function effect() {
            const response = await handleFetch("/get/modulenames", "application/json");
            try {
                const data = await JSON.parse(response);
                setModules(data);
            } catch {
                alert(response);
            }
        }
        effect();
    }, []);

    /**
     * This `<form>` is used by the user to select their modules.
     * The `<option>`s in the `<datalist>` are created by mapping each string in `modules` to an `<option>` tag
     */
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
