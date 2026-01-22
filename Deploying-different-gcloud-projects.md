# Deploying to different gcloud projects

gcloud deploy requires you to have the proper default credentials set for the account and project you are deploying to  
When you are switching from one account/project to another here are the things you need to observe:

## First: Check & SET the ACTIVE ACCOUNT

```bash
gcloud auth list
```

*Typical output:*

```text
ACTIVE  ACCOUNT
        craig.cunningham@ogd.com
        craig.cunningham@ravah-dev.com
*       craig@landmanager.us
        info@floframe.io

To set the active account, run:
    $ gcloud config set account `ACCOUNT`
```

```bash
# CAUTION: *config set account* doesn't always work, see below
gcloud config set account info@floframe.io
```

**Note:** using set account doesn't always do the job -- better approach is always use:

```bash
gcloud auth login
```

... which may help avoid project quota warning issue.

## Next: Reauthenticate the application-default login

```bash
gcloud auth application-default login
```

This will open a browser and allow you to authenticate the appropriate account for this project.  
This authentication will update your application-default credentials locally:  
`/Users/craigcunningham/.config/gcloud/application_default_credentials.json`  

## Then: update the quota project

```bash
# for landmanager use:
# gcloud auth application-default set-quota-project project-landmanager

# for floframe use:
gcloud auth application-default set-quota-project bach-455721
```

## Finally, set the active project to deploy to

```bash
gcloud config set project bach-455721
# gcloud config set project project-landmanager
```

## Done

Now you should be able to deploy to the project.
