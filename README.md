AnkiHRPG
=======

Anki 2 add-on for use with HabitRPG. Automatically scores habits when you reach the end of your Anki timebox 
and when you review all cards in a deck.

For use with HabitRPG: http://habitrpg.com

Inspired by: https://github.com/Pherr/HabitRPG-Anki-Addon

Uses some code from https://github.com/Pherr/HabitRPG-Anki-Addon but scores you for reaching the end of your
timebox or reviewing all scheduled cards in a deck instead of scoring you for correct answers.

I feel that you should reward yourself for effort, not just performance. This Anki addon gives you points in
your HabitRPG account for the following:

1. No more cards to review in a deck - Scores 'Anki Deck Complete'
2. Reached a timebox? - Scores 'Anki Timebox Reached'
3. Get flashcards right? - Scores 'Anki Correct Answer' once for every five cards you remember.

*The three habits will be created automatically for you.

Set the new habits to positive only for best results.

INSTALLATION
============

The Easy Way:
In Anki, go to Tools >> Add-ons >> Browse & Install
Paste in the following code: 954979168 


Linux:

Install ankihrpg.py to $HOME/Anki/addons/ directory
Start Ank and run Tools >> Setup HabitRPG
     enter userID and apiKey from HabitRPG
     
     Habitica userID and apiKey: These are NOT your username and password! See the API section of the settings menu in habitica: https://habitrpg.com/#/options/settings/api

To set up timeboxing for Anki:
Tools >> Preferences >> Timebox time limit

Windows and Mac:

Install ankihrpg.py to [your home directory]/Documents/Anki/addons directory
Start Ank and run Tools >> Setup HabitRPG
     enter userID and apiKey from HabitRPG

To set up timeboxing for Anki:
Tools >> Preferences >> Timebox time limit


Set the new habits to positive only for best results.

USE
===

Once you set the timebox time limit, Anki will display a message when you have worked on a deck of cards for
the set amount of time. If you are connected to the internet, AnkiHRPG will give you points on HabitRPG when
Anki syncs its decks. Anki will give you the option to continue reviewing cards and present you with the 
same message after another interval of however many minutes you set the timebox time limit to and AnkiHRPG 
will again give you points.

AnkiHRPG will also give you points when you have reviewed all scheduled cards in a deck and have no more cards
to review.
     *Note: This behavior will also be triggered when you open up a deck with no cards scheduled for review.
            The scoring function is wrapped around the Anki function that displays the message saying that 
            you have no more cards to review. This pops up when you open a deck with no scheduled cards and 
            I don't know any way around the problem, but it isn't a big deal to me.
            
            
Set the new habits to positive only for best results.
