import React, { useState, useEffect } from 'react';
import handleFetch from '../../functions/handleFetch';

const {
    REACT_APP_HOMEPAGE,
    REACT_APP_SERVER_URL
} = process.env;


/**
 * 
 * @param {Array} props.chosenModules `chosenModules` from the `<ModulesChooser/>` component.
 */
function Calendar(props) {

    // https://docs.mobiscroll.com/react/eventcalendar

    // https://reactjsexample.com/react-calendar-component-with-support-for-multiple-views-and-events/

    // https://fullcalendar.io/demos

    const [ moduleTimetables, setModuleTimetables ] = useState([]); // array of objects

    // requests the timetables for each chosen module
    useEffect(
        () => {
            if (typeof props.chosenModules === "undefined")
                return;

            if (props.chosenModules.length === 0) {
                setModuleTimetables([]);
                return;
            }

            // fetching the module timetables
            async function effect() {
                try {
                    const mappedModuleCodes = props.chosenModules.map(s => s.split(" - ")[0]);
                    const response = await fetch(REACT_APP_SERVER_URL + "/get-module-timetables", {
                        method: 'POST',
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify(mappedModuleCodes)
                    });
                    const data = await response.json();
                    setModuleTimetables(data);
                } catch (e) {
                    alert(e);
                }
            }
            effect();
        },
        [props.chosenModules]
    );

    // useEffect(() => console.log("props.chosenModules:", props.chosenModules), [props.chosenModules])
    // useEffect(() => console.log("moduleTimetables:", moduleTimetables), [moduleTimetables])

}

export default Calendar;