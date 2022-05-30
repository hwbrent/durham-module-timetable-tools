function func1() {
    // url = https://timetable.dur.ac.uk/week_patterns.htm

    // will store all the content of the table
    // will be a 2d array, where each subarray is a row in the table
    let weekPatternsArray = [];

    // iterate through each <tr> (i.e. row) of the table
    for (let tr of document.getElementsByTagName("tr")) {

        // the header of the table looks like this:
        /*
        +–––––––––––––––––––––––––––––+––––––––––––––––––––––+
        |       Syllabus Weeks        |   Durham Weeks       |
        +–––––––––––––+–––––––––––––––+––––––+–––––––––––––––+
        | Week Number | Calendar Date | Term | Teaching Week |
        +–––––––––––––+–––––––––––––––+––––––+–––––––––––––––+
        */

        // `arr` stores the value of each row in the table
        // arr[0] --> Week Number
        // arr[1] --> Calendar Date
        // arr[2] --> Term
        // arr[3] --> Teaching Week
        
        const arr = [];

        // iterates through each of the four <td> elements in the current <tr> (i.e. table row)
        for (let td of tr.getElementsByTagName("td")) {
            // adds the content of the <td> to `arr`
            arr.push(td.textContent);
        }

        weekPatternsArray.push(arr);
        // console.log(arr);
        // console.log("\n");
    }

    weekPatternsArray.splice(0,1);
    weekPatternsArray.splice(0,1);

    const academicYear = document.querySelector(".l2sitename").textContent.trim().split(" ")[0];
    const lower = academicYear.split("-")[0];
    const upper = lower.slice(0,2) + academicYear.split("-")[1];

    weekPatternsArray.push([lower, upper]);

    console.log(weekPatternsArray);
}

function func2() {

    let weekPatternsObj = {};

    // figuring out the academic year span
    const academicYear = document.querySelector(".l2sitename").textContent.trim().split(" ")[0];
    const lower = academicYear.split("-")[0];
    const upper = lower.slice(0,2) + academicYear.split("-")[1];
    // console.log(lower);
    // console.log(upper);

    weekPatternsObj["Year Span"] = {
        "lower": lower,
        "upper": upper
    }

    // iterate through each <tr> (i.e. row) of the table
    for (let tr of Array.from(document.getElementsByTagName("tr")).slice(2)) {

        const tds = tr.getElementsByTagName("td");

        console.log(tds);

        // tds[0].textContent --> Week Number
        // tds[1].textContent --> Calendar Date
        // tds[2].textContent --> Term
        // tds[3].textContent --> Teaching Week

        // the values in the row
        const subObj = {
            "Calendar Date": tds[1].textContent,
            "Term": tds[2].textContent,
            "Teaching Week": tds[3].textContent
        }
        
        const weekNumber = tds[0].textContent.split(" ")[1];

        weekPatternsObj[weekNumber] = subObj;
    }
    console.log(weekPatternsObj);
}

func1();