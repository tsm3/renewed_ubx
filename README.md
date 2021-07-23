# UBX API for RENEW's RCB_F9T
## Notes:
- Do I wanna change the Event's for Condition variables??
  - This could maybe make things cleaner? although I'd be less used to them so it'd make implementation more 
    difficult and I probably wouldn't use them right
- The _single_send_poll() method worked, but I'm not convinced it's _correct_ still
- msg.identity -> CFG-VAL{GET, SET, DEL}
- msg.payload returns bytes

## Feature List:
- Stuff

- 

##TODO:
- [ ] Finish TODO
- [ ] Finish Feature List
- [ ] Figure out why UBXStreamer.set_configs() NAK's in batch mode
- [ ] Decide if I want a NAK to raise Exception or just log
- [ ] Add logging to everything (In progress)
- [ ] Figure out if ubp._live is useful or not??
- [ ] Try to improve dual variable/event system for threads (maybe use condition variables?)
- [ ] Finish single POLL message method
- [ ] Write user method for sending multiple POLL messages
- [ ] Write static func to create msgs that aren't supported by pyubx2
- [ ] Write static func to parse tp_data msgs specifically