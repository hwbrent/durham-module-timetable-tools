
// url = https://timetable.dur.ac.uk/module.htm

const moduleTimetableParameters = {}

// the data I'm looking for is in the <tr>'s (i.e. rows) of a <table>
for (let tr of document.getElementsByTagName("tr")) {

    // each row has two <td> tags; the second one contains the <select> tag which contains the <option>'s which are the parameters I'm looking for
    const tds = tr.getElementsByTagName("td");

    const optionType = tds[0].textContent;

    // the last row in the table is as below:
    // in the last <tr>, the first <td> is empty, and the second <td> is a button saying "View Timetable"
    // obviously we don't care about this <tr>, so just break out of main for loop
    if (optionType.length == 1) {
        break;
    }

    const options = [];

    // the <option>'s are in a <select> but we can simply bypass the <select> and access the <option>'s inside
    for (let option of tds[1].getElementsByTagName("option")) {
        
        // option.textContent is what is shown to the user in the webpage.
        // option.value is what we really want - this is what gets passed as a URL parameter.
        // example subArray --> ["ACCT2101 - Financial Reporting", "ACCT2101"]
        const subArray = [option.textContent, option.value]
        options.push(subArray);
    }

    moduleTimetableParameters[optionType] = options;
}

console.log(moduleTimetableParameters);
