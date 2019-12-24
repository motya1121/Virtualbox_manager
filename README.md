# Virtualbox_manager
Manage VMs registered in Virtualbox


基本的にはhomeディレクトリ配下で作業する
バックアップをとる場合 or 今は使わないは，圧縮 or tar とかでDropboxのディレクトリに配置する


## DB

|  カラム名   |  型   |                  意味                  |
| :---------: | :---: | :------------------------------------: |
|    uuid     | TEXT  |          vboxのuuidを格納する          |
| backup_date | TEXT  |     バックアップした日付を格納する     |
|   machine   | TEXT  | バックアップしたマシンの名前を格納する |