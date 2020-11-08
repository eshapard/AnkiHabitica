# AnkiHabitica

Anki 2.1 add-on for use with Habitica. Places a progress bar on the bottom of the review screen and scores a Habitica habit when the progress bar reaches the end. Also shows your health, exp, and mana stats as percentages to the right of the progress bar.

For Anki 2.0 see branch [anki2.0](https://github.com/eshapard/AnkiHabitica/tree/anki2.0)

For use with Habitica: http://habitica.com

AnkiHabitica places a progress bar on the bottom of the review screen.

![](https://github.com/eshapard/AnkiHabitica/blob/master/AnkiHabitica_progbar.png?raw=true)

* Progress Bar: Progresses as you answer cards, complete decks, etc.
* Health %: Your Habitica avatar's health as a percentage.
* XP %: Your Habitica avatar's experience points as a percentage of points needed to level up.
* Mana %: Your Habitica avatar's mana points as a percentage.

As you review, you earn points by answering questions, (optionally) hitting timeboxes, and (optionally) clearing decks.

* 'Timeboxes' are hard-coded as 15 minutes of time spent reviewing cards. You may set your Anki timebox to whatever you like, but for this add-on to keep track of how many timeboxes you've earned, I had to set a hard-coded consistent timebox.

As you answer questions, your progress bar advances and once it reaches the end (12 flashcards in default), the add-on scores your Anki Points habit that will be created automatically.

* Note: if the add-on creates two habits by accident, just delete one.

After scoring your habit, a pop-up message box will tell you how many XP, HP, Mana, and Gold points you earned (if any) and it will announce if you've levelled up and if you've received any items...

![](https://github.com/eshapard/AnkiHabitica/blob/master/AnkiHabitica_msgbox.png?raw=true)

## INSTALLATION

### Auto Installation

1. In Anki, go to Tools >> Add-ons >> Browse & Install
2. Paste in the following code: 1758045507
3. Restart Anki
4. After restart, go to Tools >> Ankihabitica >> Setup
5. Open the Habitca API Settings page: https://habitica.com/user/settings/api
6. Enter *User ID* and *API Token* that get from HabitRPG
7. A new Habitica Habit will be created called Anki Points (after you do some cards!)

### Manual Installation

1. Download the add-on file in https://github.com/eshapard/AnkiHabitica/releases
2. Start Anki and in "Tools >> Add-ons >> Install from files..." select file that you download in the previous step.
3. Then follow [step 3 to step 7 in Auto Installation](https://github.com/eshapard/AnkiHabitica#the-easy-way)

## Tools Menu >> AnkiHabitica

After installation, you'll find a sub-menu called *AnkiHabitica* under the Tools menu.

* Setup Anki Habitica: Enter your Habitica userID and APItoken.
* Score Habitica Backlog: When you've earned a lot of points on another device, AnkiHabitica will catch up by scoring your habit up to three times in a row each time the progress bar reaches the end. To process the backlog in one fell swoop, run this item.
* Refresh Habitica Avatar: In testing this addon, I noticed that occasionally the avatar I downloaded would look a little funky. This is probably due to occasional changes Habitica makes to the image files; which can cause temporary problems. Run this menu item to re-download the avatar again, hopefully getting the correct image this time.

## Frequently Asked Questions

### How can I use AnkiHabitica in AnkiDroid?

The AnkiHabitica only runs on the desktop version of Anki, but as long as you sync your reviews on both ankidroid and the desktop version with ankiweb, the add-on will catch all the reviews.

For version before Anki 2.1.20, you will need to sync your desktop version of Anki with Habitica manually. To do this, simply access the Tools menu from Anki desktop. Then go to AnkiHabitica > Score Habitica Backlog.

If you use newer Anki, addon will automatically score backlog after syncing.

### Why are there some weird text in the notes of the Habit

That's how the addon keeps track of things across multiple devices and multiple sessions.
You must keep that there.

## Notes

AnkiHabitica stores some necessary information in the notes field of your Habitica habit. Do not edit the notes field unless you really know what you're doing.

The *Score Habitica Backlog* function is limited to scoring your habit a maximum of 25 times in a row. This is to prevent the application from appearing to hang; causing the user to think Anki has crashed. In future versions, I may implement a progress bar notification, but for now, this is how it is.

Apparently, video game players start to get impatient when the progress bar is around 80% or so. If you speed up how quickly they acquire points after 80%, you'll get a higher retention rate of players. See Tom Chatfield's TED talk for more: [https://www.ted.com/talks/tom_chatfield_7_ways_games_reward_the_brain?language=en](https://www.ted.com/talks/tom_chatfield_7_ways_games_reward_the_brain?language=en)

AnkiHabitica's progress bar emulates this behavior. After the bar reaches about 80%, it will progress twice as fast as it normally does.

## General Anki Tips

I occasionally post tips on using Anki and calibrating its settings at https://eshapard.github.io/anki/
