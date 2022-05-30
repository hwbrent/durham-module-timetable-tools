import React, { useState, useEffect } from 'react';
import handleFetch from '../../functions/handleFetch';

import ModulesChooser from '../ModulesChooser.jsx';

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


    return (
        <>
        <h1>This is the home page</h1>
        <hr/>
        <div>
            <ModulesChooser/>
        </div>
        </>
    );

}