# HAPPY NOTES
#### Video Demo:  [<URL HERE>](https://youtu.be/pc_BTavxdWo)
## Description:

### Overview and Inspiration
Happy Notes is my personal project, made by me, LanderYT. At the start of the year of 2024, I have made a new year resolution to write the important things of my days down somewhere, but I have failed very early. Therefore, I wanted to make an application that makes it slightly easier for users to jot down their happy/unhappy thoughts at the end of the day.

Happy Notes is a Flask application, in other words, a kind of website. The application allows users to create and use their own accounts stored on our database tables (sqlite3). Once user is done with their registration, they have access to writing down their happy thoughts, but user is limited to one note per day, according to their timezone. User can also edit their already written notes, as well as outright deleting some. Moreover, user is also able to download their entire table of notes in a csv format file. Finally, the application makes changing displayname on homepage, personal bio and other information, possible.

### Registration
The registration page asks the user for a login username, password, confirm password. It also requires user to provide a displayname, which the Flask application will use to greet the user once they get to the index page. We also require users to provide a magic word so that they can reset their password, should they forget it. Finally, the page demands the user's timezone, so that the application can accurately determine when a new day starts for a specific user.

The registration page makes use of JavaScript as a client-side validator for the inputs. User will not be able to register with a password shorter than 6 characters, nor leave any fields empty. The entire application also has a well-made backend validation system as a final line of defense in case of JavaScript not being enough for mischievous users.

Finally, when user has finished their registration process, they will be redirected to the index page.

### Login
This page asks user for their registered username (which they will no longer be able to change) and password. It also gives the option of "Forget password", where user can use their magic word to change their password.

Login page is likely the first page the user stumbles upon when they go to the website for the first time, and it's functionalities are similar to that of register.

### Homepage / Index Page
Homepage greets user with their desired displayname upon accessing. User can also see a "streak" indicating how many consecutive days they have been writing notes. If there are no notes written within up to 48 hours (depending on timezones) of the user, their streak will be lost.

If user has yet to write a note for the current date, homepage will display a few input fields where user can enter information about their day, such as the day's rating and description. Otherwise, the page will inform the user how long until they are able to write the next note.

### Edit
Upon accessing the page, the user will see a single date input, where they can select a date of their note. If the date the user submitted contains a note from the user, they will be transferred to a secondary "editing" page using a new session token of the note's ID. Otherwise, user will receive an apology for a date that has no notes.

In the editing page, after selecting the correct date, user will see a similar input field to the index page when writing their note, except they will also notice a single row table containing the information about their note. One interesting thing about this table is that rating will be colored depending on the value of the rating. Finally, at the bottom of the editing page, there is also a "Remove" button if user wishes to remove the note altogether. Do note that this action will reset the user's current streak due to the system unable to find the latest note within the given time scope.

### View
View page does a very simple thing: Lets users view their notes in an HTML table. Similar to Edit, the rating will be colored depending on the value of the note's rating.

However, I've added an Edit button at the end of each row of notes, which sends user directly to the editing page (that already has the note's info), instead of edit. Finally, there is a big green button at the middle of the screen where users can download their entire table of notes in CSV file format. I am planning to add xls and other table formats in the future.

### Settings
Upon reaching the page, user will be greeted with 2 cards: Info and Security.

#### Info
This page allows user to personalize and modify their information from their registration, such as timezone, displayname and bio. There is currently no real use for the user's bio besides viewing it themselves in settings, unfortunately. However, if user decides to change displayname, the homepage/index page will greet them with the new displayname upon access. Last but not least, user can change their timezone if they happen to move or travel and want to continue using our services, nevertheless, if the user changes their timezone, their current streak will be lost to prevent exploits.

#### Security
This page is pretty straightforward. User can change their password and their magic word.

## Conclusion
That's the end of our documentation, thank you for reading and hope you enjoy my project!

