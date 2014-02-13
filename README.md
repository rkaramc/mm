mm
==

`mm` is the executable that powers MavensMate Force.com IDEs. You can use `mm` to perform every important task relative to developing on the Force.com platform. For example, to compile a project:

```
$ mm compile_project
```

You can also use `mm` to provide a default UI for tasks like creating a new project, editing a project, running unit tests & anonymous apex, & deploying metadata to servers. Just use the --ui flag:

```
$ mm new_project --ui
```

In order to provide context to your operation, pipe json to `mm` via STDIN. For example:

```
$ mm compile_project <<< '{ "project_name" : "myproject" }'
```

### Command Line Arguments

<table>
  <tr>
    <th>Argument</th><th>Description</th>
  </tr>
  <tr>
    <td>-o</td><td>Requested Operation (optional)</td>
  </tr>
  <tr>
    <td>-c</td><td>Plugin client making the request ("Sublime Text" [default], "TextMate", "Notepad++", etc.)</td>
  </tr>
  <tr>
    <td>--ui</td><td>Launch the base UI for the operations</td>
  </tr>
</table>

### Supported Operations

All supported commands can be found here: <a href="https://github.com/joeferraro/mm/tree/master/lib/commands">https://github.com/joeferraro/mm/tree/master/lib/commands</a>

<table>
  <tr>
    <th>Operations</th><th>Description</th>
  </tr>
  <tr>
    <td>new_project</td><td>Creates a new project</td>
  </tr>
  <tr>
    <td>edit_project</td><td>Edits contents of a project</td>
  </tr>
  <tr>
    <td>upgrade_project</td><td>Upgrades a project</td>
  </tr>
  <tr>
    <td>compile_project</td><td>Compiles a project</td>
  </tr>
  <tr>
    <td>new_metadata</td><td>Creates new metadata</td>
  </tr>
  <tr>
    <td>refresh</td><td>Refreshes files and/or directories from the server</td>
  </tr>
  <tr>
    <td>clean_project</td><td>Reverts a project to server state based on package.xml</td>
  </tr>
  <tr>
    <td>compile</td><td>Compiles files and/or directories</td>
  </tr>
  <tr>
    <td>delete</td><td>Deletes metadata from the server</td>
  </tr>
  <tr>
    <td>get_active_session</td><td>Retrieves an active Salesforce.com session</td>
  </tr>
  <tr>
    <td>update_credentials</td><td>Updates the credentials associated with a project</td>
  </tr>
  <tr>
    <td>execute_apex</td><td>Executes a block of Apex</td>
  </tr>
  <tr>
    <td>deploy</td><td>Deploys metadata to one or more destination orgs</td>
  </tr>
  <tr>
    <td>test</td><td>Runs Apex unit tests</td>
  </tr>
  <tr>
    <td>list_metadata</td><td>Lists metadata of a certain type</td>
  </tr>
  <tr>
    <td>index_metadata</td><td>Indexes project metadata</td>
  </tr>
  <tr>
    <td>list_connections</td><td>List org connections for this project</td>
  </tr>
  <tr>
    <td>new_connection</td><td>Creates a new org connection</td>
  </tr>
  <tr>
    <td>delete_connection</td><td>Deletes an org connection</td>
  </tr>
  <tr>
    <td>index_apex_overlays</td><td>Indexes Apex checkpoints</td>
  </tr>
  <tr>
    <td>new_apex_overlay</td><td>Creates a new Apex checkpoint</td>
  </tr>
  <tr>
    <td>delete_apex_overlay</td><td>Deletes an Apex checkpoint</td>
  </tr>
  <tr>
    <td>fetch_logs</td><td>Fetches most recent Apex debug logs for this user</td>
  </tr>
  <tr>
    <td>fetch_checkpoints</td><td>Fetches most recent Apex checkpoints for this user</td>
  </tr>
  <tr>
    <td>new_project_from_existing_directory</td><td>Creates a new project from an existing directory</td>
  </tr>
  <tr>
    <td>open_sfdc_url</td><td>Opens metadata in Salesforce</td>
  </tr>
   <tr>
    <td>index_apex</td><td>Indexes Apex metadata for a project</td>
  </tr>
   <tr>
    <td>update_subscription</td><td>Updates metadata subscription for a project</td>
  </tr>
   <tr>
    <td>new_log</td><td>Creates a new Apex debug log</td>
  </tr>

</table>

