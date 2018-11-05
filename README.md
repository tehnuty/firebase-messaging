# Firebase-messaging for humans

Simple use (send to one topic):
```python
firebase_response = firebase.send_notification(push_topic=topic,
                                                       title=card.card_title,
                                                       body=card.notification_text,
                                                       action=push_action,
                                                       card_id=card.sid())                                                      
```

Send to all:
```python
firebase_response = firebase.send_notification(send_to_all=True,
                                                       title=card.card_title,
                                                       body=card.notification_text,
                                                       action=push_action,
                                                       card_id=card.sid())
```
Silent push:
```python
translated_id = account_id.translate(None,":")
firebase.send_notification(action=PushActions.SILENT_UPDATE_ACCOUNT,
                                           push_topic=translated_id,
                                           device_id=device_id,
                                           silent=True,)
```
