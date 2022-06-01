import React from 'react';

function ChosenModuleList(props) {

    const lis = props.chosenModules.map((value,index) => {

        // the button to delete the option from `chosenModules`.
        const deleteButton = <button type="button" onClick={props.handleDeleteButtonClick}>🗑️</button>

        // the main <li> (which contains `deleteButton`)
        const li = <li key={index}>{value} | {deleteButton}</li>;

        return li;
    });

    const ul = <ul>{lis}</ul>;

    return ul;
}

export default ChosenModuleList;