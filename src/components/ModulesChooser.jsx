import React, { useState, useEffect } from 'react';
import handleFetch from '../functions/handleFetch';

import ModulesDatalist from './ModulesDatalist';
import ModulesCalendar from './ModulesCalendar';

// ==============================

function ModulesChooser() {

    // `chosenModules` is the list of module names chosen by the user
    const [ chosenModules, setChosenModules ] = useState([]);

    // --------------------

    // logs `chosenModules`, but only if the value of `chosenModules` changes.
    useEffect(
        () => {
            console.log("chosenModules:");
            console.log(chosenModules);
        },
        [chosenModules]
    )

    // --------------------

    // "deletes" (i.e. filters out) the chosen module <li> that's been clicked on
    const handleDeleteButtonClick = ({target}) => {
        setChosenModules(prev => prev.filter(el => (el.key != target.key)))
    }

    // maps each chosen module to a <li> with a delete button
    const chosenModulesList = chosenModules.map((value, index) => {
        const deleteButton = <button type="button" onClick={handleDeleteButtonClick}>🗑️</button>;
        return <li key={index}>{value}{deleteButton}</li>;
    });

    // --------------------

    /**
     * This event handler gets the value of the <ModulesDatalist/> `<input>` tag.
     * If the `inputValue` a valid module and it's not already in `chosenModules`, it adds it.
     */
    const handleDatalistFormSubmit = (event, modules) => {
        event.preventDefault();

        // get value from text input element
        const inputElement = event.target.getElementsByTagName("input")[0];
        const inputValue = inputElement.value;

        setChosenModules(prev => {
            if (!modules.includes(inputValue)) {
                window.alert("Please select a module from the list provided");
                return prev;
            } else if (prev.includes(inputValue)) {
                return prev;
            } else {
                return [...prev, inputValue];
            }
        });
    }

    // --------------------

    return (
        <>
        <ul>
            {chosenModulesList}
        </ul>

        <hr/>

        <ModulesDatalist handleFormSubmit={handleDatalistFormSubmit}/>

        <hr/>

        <ModulesCalendar chosenModules={chosenModules}/>
        </>
    );
}

export default ModulesChooser;
