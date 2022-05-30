import React from 'react';

const envVariables = process.env;
const {
    REACT_APP_HOMEPAGE,
    REACT_APP_SERVER_URL
} = envVariables;

export default function LoginPage() {

    const handleSubmit = async (event) => {
        event.preventDefault();

        // retrive the values from the below <input> tags
        const [ cisUsernameInputEl, passwordInputEl ] = event.target.getElementsByTagName("input");
        const cisUsername = cisUsernameInputEl.value;
        const password = passwordInputEl.value;

        // reset the values of the <input> fields
        // event.target.getElementsByTagName("input")[0].value = "";
        // event.target.getElementsByTagName("input")[1].value = "";

        // const url = `${process.env.REACT_APP_SERVER_URL}/validate/${cisUsername}/${password}`;
        const url = `${REACT_APP_SERVER_URL}/validate/${cisUsername}/${password}`;
        const response = await fetch(url, {
            method: "GET",
            headers: {"Content-Type": "application/json"}
        });

        // either `true` or `false`
        const userIsValid = await response.json();

        console.log("userIsValid:", userIsValid);
        alert(userIsValid);
    }

    // ---------------

    return (
        <>
            <h1>Please login below to use this website</h1>
            <p><b>NB: this information is not stored anywhere or shared with anyone.</b></p>

            <hr/>

            <form onSubmit={handleSubmit}>
                <label>
                    CIS Username:
                    <input required type="text" placeholder="e.g. abcd12"/>
                </label>
                <br/>
                <label>
                    Password:
                    <input required type="password"/>
                </label>
                <br/>
                <input type="submit"/>
            </form>
        </>
    );
}