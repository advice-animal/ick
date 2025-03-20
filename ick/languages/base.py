#     def sync_modified_file(self, mod: Modified):
#         """
#         This means that a previous rule did modify this file.
#
#         Only sent when the previous rule does not share a working copy.
#         """
#         if mod.new_bytes is None:
#             os.remove(mod.filename)
#         else:
#             Path(mod.filename).write_bytes(mod.new_bytes)
#
#     def work_on_files(self, filenames) -> Generator[Msg, None, None]:
#         raise NotImplementedError()
#
#     def serve(self):
#         assert not sys.stdin.isatty()
#         for line in sys.stdin.buffer:
#             msg = decode(line, type=Msg)
#             if isinstance(msg, Done):
#                 return
#             elif isinstance(msg, Modified):
#                 self.sync_modified_file(msg)
#             #
#             # elif isinstance(msg,
#
#
# def get_impl(language: str, rule_dir: str, name: str):
#     module_name = "ick.languages." + language
#     __import__(module_name)
#     return sys.modules[module_name].Language(rule_dir, name)

