// SETING UP SOCKETIO
var chats = {};
var messageId = 0;

var socket = io.connect('http://' + document.domain + ':' + location.port + '/');
socket.on('connect', function() {
	socket.emit('chat_connection', {data: 'I\'m connected!'});
	console.log('CONNECTED TO SOCKET');
});

socket.on('received', function(data) {
	console.log('user id :' + socket.user_id);
	console.log(data);
})

function sendMessage(e) {
	var message = $('#message_to_' + e.data).val();
	$('#message_to_' + e.data).val('');
	console.log('SENDED ' + message + ' to ' + e.data);
	socket.emit('send_to', {id: e.data, content: message});
	$('#chatting_' + e.data + ' .messages-wrapper').append($('#one-message-model').clone().prop('id', 'mess_' + messageId));
	$('#mess_' + messageId + ' .one-message-content').text(message);
	$('#mess_' + messageId + ' .message-emitter').text(e.data);
	messageId = messageId + 1;
}

function launchChat(e) {
	$('#currentChatsWrapper').append($('#currentChatModel').clone().prop('id', 'chatting_' + e.data.id));
	$('#chatting_' + e.data.id + ' .on-chat-button').text(e.data.username);
	$('#chatting_' + e.data.id + ' .send-message-button').prop('id', 'send_to_' + e.data.id);
	$('#chatting_' + e.data.id + ' .message-content').prop('id', 'message_to_' + e.data.id);
	$('#chatting_' + e.data.id + ' .send-message-button').on('click', e.data.id, sendMessage);
}

//Load matches for chat
function loadChatMatches() {
	var matchesReq = new XMLHttpRequest();
	matchesReq.open('GET', '/load_chat');
	matchesReq.onreadystatechange = function() {
		if (matchesReq.readyState == 4 && matchesReq.status == 200) {
			matches = JSON.parse(matchesReq.responseText);
			console.log(matches);
			for (var match in matches) {
				if (matches.hasOwnProperty(match)) {
					console.log(matches[match].username + ' has id :' + matches[match].id);
					var itemId = 'chat_' + matches[match].id
					$('#chat_container').append($('#chatterModel').clone().prop('id', itemId));
					$('#' + itemId).text(matches[match].username);
					$('#' + itemId).on('click', matches[match], launchChat)
				}
			}
		}
	}
	matchesReq.send();
}

loadChatMatches();