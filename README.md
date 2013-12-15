AnkiRPG
=======

Anki 2 add-on for use with HabitRPG. Automatically scores habits when you reach the end of your Anki timebox 
and when you review all cards in a deck.

For use with HabitRGP: http://habitrpg.com

Inspired by: https://github.com/Pherr/HabitRPG-Anki-Addon

Uses some code from https://github.com/Pherr/HabitRPG-Anki-Addon but scores you for reaching the end of your
timebox or reviewing all scheduled cards in a deck instead of scoring you for correct answers.

I feel that you should reward yourself for effort, not performance. Once the other project is fixed, I
suppose you could use both addons at the same time if you wanted to reward yourself for both performance and
effort.

INSTALLATION
============

Install to $HOME/Anki/addons/ directory
Start Ank and run Tools >> Setup HabitRPG
     enter userID and apiKey from HabitRPG

To set up timeboxing for Anki:
Tools >> Preferences >> Timebox time limit

USE
===

Once you set the timebox time limit, Anki will display a message when you have worked on a deck of cards for
the set amount of time. If you are connected to the internet, AnkiRPG will give you points on HabitRPG. Anki
will give you the option to continue reviewing cards and present you with the same message after another 
interval of however many minutes you set the timebox time limit to and AnkiRPG will again give you points.

AnkiRPG will also give you points when you have reviewed all scheduled cards in a deck and have no more cards
to review.
     *Note: This behavior will also be triggered when you open up a deck with no cards scheduled for review.
            The scoring function is wrapped around the Anki function that displays the message saying that 
            you have no more cards to review. This pops up when you open a deck with no scheduled cards and 
            I don't know any way around the problem, but it isn't a big deal to me.
            
