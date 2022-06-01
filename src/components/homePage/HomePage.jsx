import React, { useState, useEffect } from 'react';
import handleFetch from '../../functions/handleFetch';

import ChosenModuleList from './ChosenModuleList';
import ModulesDatalist from './ModulesDatalist';
import Calendar from './Calendar';

const {
    REACT_APP_HOMEPAGE,
    REACT_APP_SERVER_URL
} = process.env;

/**
 * The Home Page of the app.
 * @summary 
 * @returns React Component
 */
export default function HomePage() {

    // `chosenModules` is the list of module names chosen by the user
    const [ chosenModules, setChosenModules ] = useState([]);

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

    const handleDeleteButtonClick = ({target}) => {
        setChosenModules(prev => prev.filter(value => value.key !== target.key));
    }

    return (
        <>
        <h1>This is the home page</h1>

        <hr/>

        <ChosenModuleList chosenModules={chosenModules} handleDeleteButtonClick={handleDeleteButtonClick}/>

        <ModulesDatalist handleFormSubmit={handleDatalistFormSubmit}/>

        <Calendar chosenModules={chosenModules}/>
        </>
    );
}
