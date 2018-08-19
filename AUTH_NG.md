The auth\_ng authentication module works based on a system of tags. To
authenticate an action, a user's tags are queried sequentially.
If at any point a tag returns AuthRes.SUCCESS, the action is permitted.
If a tag returns AuthRes.FAIL, the action is forbidden. Returning
AuthRes.CONTINUE causes the other tags to be considered, and is the
default.

Tags are represented textually as tag_name{:tag_args}...
For example, the module tag allowing access to the core module is
represented as 'module:core'. The all tag, which always allows an
action, is represented simply as 'all'.

Currently, three tags exist: the all tag, the module tag and the command
tag. These allow access for all actions, actions in a given module and
a given command, respectively.

In the configuration file, tags can be set in the "user_tags"
dictionary.
