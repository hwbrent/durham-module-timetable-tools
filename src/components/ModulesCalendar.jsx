import React, { useState, useEffect } from 'react';
import handleFetch from '../functions/handleFetch';

const {
    REACT_APP_HOMEPAGE,
    REACT_APP_SERVER_URL
} = process.env;

// https://docs.mobiscroll.com/react/eventcalendar

function ModulesCalendar(props) {
    // props should include `chosenModules` from the <ModulesChooser/> component

    const [ moduleTimetables, setModuleTimetables ] = useState({});

    // requests the timetables for each chosen module
    useEffect(
        () => {
            if (props.chosenModules.length === null)
                return;

            // fetching the module timetables
            async function effect() {
                try {
                    const mappedModuleCodes = props.chosenModules.map(s => s.split(" - ")[0]);
                    const response = await fetch(REACT_APP_SERVER_URL + "/getmoduletimetables", {
                        method: 'POST',
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify(mappedModuleCodes)
                    });
                    const data = await response.json();
                    await setModuleTimetables(data);
                } catch (e) {
                    alert(e);
                }
            }
            effect();
        },
        [props.chosenModules]
    );

    useEffect(() => {}, [moduleTimetables])

}

export default ModulesCalendar;