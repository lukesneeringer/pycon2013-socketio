// ---------------------------------------------------------
// -- JavaScript supporting the SocketIO Proof of Concept --
// --   author: Luke Sneeringer, luke@sneeringer.com      --
// --   license: New BSD                                  --
// ---------------------------------------------------------

$(document).ready(function() {
    // Ask for a username.
    // Note that there is *no* authentication. This is purely a proof
    //   of concept. There's also nothing to prevent two (or more) people
    //   from using the same username. We ask for a username, and blindly
    //   trust the response.
    // The purpose of this repository is to show how socket.io works,
    //   not to mess with user auth.
    var user_name = ''
    while (user_name.length === 0) {
        user_name = window.prompt('Please enter a user name: ')
    }


    // Connect to the SocketIO server when the page loads,
    //   even if I'm not asking for anything yet.
    // Once the connection is made, we tell it what our username is.
    // An important thing to note here: The "socket.io" segment of the URL
    //   is left off. This is not a traditional URL. We include just the
    //   host, followed by the namespace. If you point to "/socket.io/chat/",
    //   it won't work, because it will see that entire thing as the namespace.
    //   This is extremely counter-intuitive, so take note of it.
    socket = io.connect('http://localhost:8000/chat')
    socket.on('connect', function() {
        // `socket.emit` is the primary way that we send things to the
        //   server.
        // The first argument (here: "nick") is used most basically
        //   as a method lookup within the namespace; this will cause the
        //   ChatNamespace class will run the `on_nick` method.
        // For the other side of this concept, scroll down to the bottom
        //   of this file (or search for "socket.on" in your text editor).
        socket.emit('nick', user_name)
    })


    // Function to activate a room.
    // This causes one room to become active and all other rooms
    //   to become inactive.
    var activate_room = function(room_name) {
        // Make all of the rooms hidden, then make the room with this
        //   `room_name` un-hidden.
        $('.room').each(function() {
            $(this).parent().hide()
        })
        $('.room[data-name="' + room_name + '"]').parent().show()

        // Make all of the tabs inactive, then make the tab with this
        //   `room_name` active.
        $('.room-tab').each(function() {
            $(this).removeClass('active')
        })
        $('.room-tab[data-name="' + room_name + '"]').addClass('active')
    }


    // Function to get the active room.
    var get_active_room = function() {
        var $room_tab = $('.room-tab.active')
        if ($room_tab.length > 0) {
            return $room_tab.attr('data-name')
        }
        return null
    }


    // Hook up the control that joins a new room.
    $('#join-room').click(function(ev) {
        ev.preventDefault()

        // Get the room name to join. Then emit a message to join it.
        // Remember, this maps to the `on_join` method on the Python
        //   namespace. That method emits "room_joined", which I'm now
        //   receiving here too.
        // Note `socket.once` instead of `socket.on`. The former is simply
        //   an implementation of the latter that removes the listener on
        //   the first receipt.
        var room_name = ''
        while (room_name.length === 0) {
            room_name = window.prompt('Enter a chat room name: ')
        }

        // Next, I'm defining what I want to happen when I get an event for
        //   this room. There's nothing magic here, and this segment doesn't
        //   actually hook this function up to anything (that happens at
        //   the bottom -- `socket.on`).
        // I will *also* want to process the previous things said in the room
        //   -- the backlog -- when I join, so I want this function to already
        //   be defined so I can call it on the backlog that we get when
        //   we successfully join the room.
        var on_room_event = function(ev) {
            var $room = $('.room[data-name="' + room_name + '"]')
            
            // This is a bit tricky. The room might not exist in our DOM
            // yet, so call this function recursively on a timeout until
            // it is.
            if ($room.length === 0) {
                window.setTimeout(function() {
                    on_room_event(ev)
                }, 100)
                return
            }

            // add the event row to the room table
            var $row = $('<tr/>')
                .addClass('event')
                .addClass(ev.type)
                .appendTo($room)

            // This section just builds the HTML to display the events.
            if (ev.type === 'statement') {
                // Add a block of HTML with the speaker and message.
                $('<td/>')
                    .addClass('speaker')
                    .text(ev.user)
                    .appendTo($row)
                $('<td/>')
                    .addClass('message')
                    .text(ev.message)
                    .appendTo($row)
                $('<td/>')
                    .addClass('timestamp')
                    .text(ev.timestamp)
                    .appendTo($row)
                // Color code things from the user and mentioning the user
                // The odd CSS class names are from built-in Bootstrap styles
                if (ev.user === user_name) {
                    $row.addClass('warning')
                } else if (ev.message.toLowerCase().indexOf(user_name.toLowerCase()) !== -1) {
                    $row.addClass('success')
                }
            }
            else {
                // Add a simple event notification for whatever it is
                // that happened.
                $row.addClass('info')
                $('<td/>')
                    .attr('colspan', '2')
                    .addClass('message')
                    .text(ev.message)
                    .appendTo($row)
                $('<td/>')
                    .addClass('timestamp')
                    .text(ev.timestamp)
                    .appendTo($row)

            }

            $room.parent().stop().animate({'scrollTop': $room.height()})

            // One last thing: if the event was a topic change, then we
            // must edit the room's topic at the top segment.
            if (ev.type === 'topic_set') {
                $room.find('.topic').text(ev.topic)
            }
        }

        socket.emit('join', room_name)
        socket.once('room_joined', function(ev) {
            // This is just run-in-the mill jQuery stuff.
            //   (and this is a bit hackier than necessary since this stuff
            //   isn't the focus of this app.)

            // Add the actual HTML representing the room.
            var $room = $('<table/>')
                .addClass('table')
                .addClass('table-striped')
                .addClass('room')
                .attr('data-name', room_name)
                .appendTo($('#rooms'))
                .wrap('<div class="room-wrapper"/>')

            // Now add the tab for the room in the nav.
            $('<li/>')
                .addClass('room-tab')
                .attr('data-name', room_name)
                .append('<a href="#">' + room_name + '</a>')
                .prependTo($('#room-nav'))

            // Now add the room topic. If there is no topic, then
            // add placeholder indicating lack of a topic.
            $('<div/>')
                .addClass('topic')
                .text(ev.room.topic.length ? ev.room.topic : '(No topic set.)')
                .prependTo($room)
                .wrap('<thead/>')
                .wrap('<tr/>')
                .wrap('<th colspan=3"/>')

            // Add the table body where we'll stick the event rows.
            $('<tbody/>').appendTo($room)

            // Hide the "nothing" placeholder room, if it's not
            // already hidden.
            $('#nothing').hide()
            $('#input').show().find('input').focus()

            // Activate this room.
            activate_room(room_name)

            // Add all the stuff in the backlog to the DOM.
            for (var i = 0; i < ev.backlog.length; i += 1) {
                on_room_event(ev.backlog[i])
            }
        })

        // The final thing we need to do is actually listen for events
        //   in this room. This is, of course, the big deal -- we want
        //   to be told about things that happen in the rooms to which
        //   we are subscribed.
        // The `self._listen` method in our Python namespace defines
        //   for is that room events come down with the event named
        //   `"%s_event" % room.id` ("foo_event", "bar_event", etc.)
        //   so we'll subscribe to that. Our handler needs to handle
        //   all possible event types that rooms send down.
        socket.on(room_name + '_event', on_room_event)
    })
        

    // Hook up the control that posts a message to a room.
    $('#send').click(function(ev) {
        ev.preventDefault()

        // Sanity Check: Are we disabled?
        // If we are, don't do anything.
        if ($(this).attr('disabled')) {
            return
        }

        // Get the message from the DOM.
        var message = $('#input input').val().trim()
        $(this).attr('disabled', 'disabled')

        // Sanity Check: Is there a message? If nothing has been written,
        //   then we don't actually want to do anything.
        if (message.length === 0) {
            return
        }

        // What is the active room right now?
        var room_name = get_active_room()
        if (room_name === null) {
            return
        }

        // Send the message to our server. Again, this is an emit
        //   on our side which will map to `on_statement` on the other.
        socket.emit('statement', room_name, message)

        // Once we get back a success, we know that our message has been
        //   delivered. This means we can make the user facing act as if
        //   delivery has happened (e.g. clear out the input box).
        // Note again the use of `socket.once` here -- this means that we only
        //   catch the event once. We aren't interested in catching future
        //   events, as this listener is re-assigned on every send.
        socket.once('statement_ok', function(data) {
            $('#input input').val('')
            $('#send').removeAttr('disabled')            
        })
    })

    // make the enter button auto-submit
    $('#input input').keypress(function(event) {
        if (event.which == 13) {
            event.preventDefault()
            $("#send").click()
        }
    })


    // Hook up the control that switches between rooms.
    $(document).on('click', '.room-tab a', function() {
        activate_room($(this).parent().attr('data-name'))
    })


    // Finally, hook up the control that lets us set topics.
    $(document).on('click', '.topic', function() {
        // Get both the new topic that we want to set, as well as
        // the currently active room.
        var new_topic = window.prompt('Set the new topic for this room: ')
        var room_name = get_active_room()
        if (room_name === null) {
            return
        }

        // Send a message to our server (another emit), setting the topic
        //   for this room.
        socket.emit('topic', room_name, new_topic)
    })


    // Spit out everything that the socket sends as an error to our
    //   JavaScript console.
    // Note that "error" is the first argument to `self.emit` in the
    //   ChatNamespace class Python-side.
    // Just as the `socket.emit` on this side maps to finding a
    //   `on_foo` method in the namespace class, so what the namespace
    //   emits wraps to a registered listener to the socket on this side,
    //   and the spelling for registering such a listener is `socket.on`.
    socket.on('error', function(data) {
        console.log(['error', data])
    })
});