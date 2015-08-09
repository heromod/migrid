# Introduction #

One of the core features of MiG is the support for easy and flexible group collaboration through the VGrid mechanisms. In short everybody can create their own virtual sub-grids in MiG and use them for virtual organizations. That is, those VGrids work just like full-blown private grids with connected users and resources, only they are dynamical entities controlled solely by the participants.


# Managing VGrids #
The creator of a VGrid automatically becomes VGrid owner and can add other users as co-owners and members and allow resources into the VGrid. Owners can additionally create sub-VGrids of the VGrid for more fine grained access control. Sub-VGrids inherit owner, member and resource access from parent VGrids, so that an owner of e.g. the eScience VGrid is also an owner of the eScience/projects VGrid.

On your VGrids page you can manage your participation in existing VGrids and create new VGrids.
Each line in the table there represents a VGrid and depending on your association you will have access to one or more actions for that VGrid.

For the ones you are not associated with you can request ownership/membership with the _add_ icons in the second and third columns respectively. The owner(s) will then decide if you should be granted that access.

If you own a VGrid you can click the corresponding toolbox icon there to open the VGrid administration panel, where you can manage associated owners, members and resources. That is, who is allowed to access and take jobs from the VGrid.
As an owner you will also have full access to all the owner and member collaboration tools in the remaining columns for that VGrid.

If you are a member of a VGrid you will have access to the member collaboration tools in the remaining columns.

Resources that are allowed in a VGrid _can_ be configured to take jobs for that VGrid but do not automatically do so. This is configured as usual on the resource configuration page.


# Collaboration Tools #
A number of collaboration tools are automatically available for all VGrids.

## Shared Files ##
VGrids have a shared folder which automatically appears as a folder with the name of the VGrid in the root of owner/member grid homes. Again using the eScience VGrid as an example, all owners and members there will have an eScience folder on their Files page and can share files and sub-folders with all other participants there.
Such shared folders are marked with a small chain on the folder icon.

Tip: If you want to point other participants in your VGrid to a shared folder, it is easy to do so from your Files page. Simply navigate to the relevant folder and use copy link address in the right-click menu on the _navigation breadcrumbs_ at the top. Then you can paste the direct URL into email or whatever communication form you prefer.


## Web Pages and Portals ##
Virtual organizations often want to have some internal and public web pages. The former are typically used for internal information and creating member portals, while the latter are e.g. used to present the organization to the public.
Owners of a VGrid can edit these private and public pages while members can only see them. Everybody can view the public pages.

## Tracker Tools, Wiki and Code Hosting ##
In order to ease a number of other typical collaboration tasks MiG provides VGrids with joint Tracker tools including a WikiWiki, an issue tracker system and a revision control system.

The Wiki supports simple and easy sharing of documentation and notes among all participants. With an inline editor and simple text formatting it is a powerful tool removing all worries about file format and availability.

The issue tracker can be used to help keep track of issues in any project related code and tasks in the virtual organization.

The code repository uses Mercurial and instructions for the use of it is available in the self-hosted readme file. Just open the Tracker, select Browse Source and click the readme file there.


## Resource Monitor ##
Finally each VGrid has a private resource monitor where owners and members can inspect the resources and jobs associated with the VGrid.