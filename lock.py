from distutils.core import setup
from Cython.Build import cythonize
import os, shutil
import argparse
# 放入项目根目录同级
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dirname", default='test', help="lock your dirname")
parser.add_argument("-i", "--ignore",default=[],help="ignore files for compile", nargs='+')
parser.add_argument("-f", "--ignore_folder",default=[],help="ignore folders for compile", nargs='+')
parser.add_argument("-v", "--py_version",default=3 ,help="python version")
args = parser.parse_args()
# 在加密过程中 build文件夹将被锁住无法复制 因此只能够加密完成后再复制其他文件

print('Locking project: --> ',args.dirname)
print('ignore files: --> ',args.ignore)
print('ignore folders: --> ',args.ignore_folder)
build_dir = 'build'
build_tmp_dir = 'tmp_build'

## 通过cythonize第一次编译工程-->(1)若编译完成判断so文件目录正确则rename并删除tmp_dir-->完成
##							-->(2)若so文件路径不正确-->以tmp_dir中的.o文件使用gcc重新编译-->删除多余文件-->完成


def get_pyfiles():
	"""
	    ** Function：compile .py to .so
	    ** authon：dq
	    ** create date：19-12-25
	"""
	py_files = []
	for a,b,c in os.walk('./'):		# 当前文件路径，目录下文件夹，目录下文件
		d = ''
		tmp_files= []
		if a.split('/')[1] != args.dirname:		 # 不是目标工程文件夹
			continue
		ignore_folder_flag = False
		for folder in args.ignore_folder:		# 是不编译文件夹
			if a[2:len(folder)+2] == folder :
				ignore_folder_flag = True
				break
		if ignore_folder_flag:
			continue

		for file in c:
			f_path = os.path.join(a, file)[2:]
			if '.' in file and file.split('.')[-1] == 'py' and f_path not in args.ignore:
				tmp_files.append(f_path)

			py_files.append(f_path)

		for t in a.split('/')[1:-1]:
			d = d + '/' + t
		#print('>>>>>>>>>>> dir:  ',d,' <<<<<<<<<<<<<<<<<<<',a)
		#try:
		setup(ext_modules=cythonize(tmp_files,compiler_directives = {'language_level': args.py_version}) ,script_args=["build_ext", "-b", build_dir+d, "-t", build_tmp_dir])
		# except:
		# 	setup(ext_modules=cythonize(tmp_files),
		# 		  script_args=["build_ext", "-b", build_dir + d, "-t", build_tmp_dir])

	if rename():
		if os.path.exists(build_tmp_dir):
			shutil.rmtree(build_tmp_dir)

	else:
		recompile()
		if os.path.exists(build_tmp_dir):
			shutil.rmtree(build_tmp_dir)

	for f in py_files:
		try:
			os.remove(f[:-3]+'.c')
		except:
			continue
	add_sources()
	print('\n\033[0;31m%s\033[0m' % 'compile success!')
	return 1


def rename():		# 目录结构对比放在rename方法中
	"""
	    ** Function：main-xxxx.so  -> main.so
	    ** return：
	    ** authon：dq
	    ** create date：19-12-25
	"""
	for a,b,c in os.walk(build_dir+'/'):
		if a in args.ignore_folder:
			continue
		if a.split('/')[1] != args.dirname:
			continue

		tmp = a.split('/')[1:]
		source_path = os.getcwd()
		for p in tmp:
			source_path = source_path+'/'+p

		for so_file in c:
			new_name = so_file.split('.')[0]+'.so'
			os.rename(a+'/'+so_file,a+'/'+new_name)
			if os.path.exists(source_path+'/'+new_name.split('.')[0]+'.py'):
				continue
			else:
				print('----------------------\n\n \033[1;44m%s\033[0m \n\n'
					  '----------------------\n\n' % ' Compile error, Recompiling...')
				return False
	return True

def add_sources():
	"""
	    ** Function：copy resource file to build dir  without .py
	    ** authon：dq
	    ** create date：19-12-25
	"""
	for a,b,c in os.walk('./'):		# 当前文件路径，目录下文件夹，目录下文件
		if a.split('/')[1] != args.dirname:
			continue
		file_path = os.path.join(os.getcwd(), os.path.join(build_dir, a[2:]))
		if not os.path.exists(file_path):
			os.mkdir(file_path)

		#################################################
		ignore_folder_flag = False
		for folder in args.ignore_folder:  # 是不编译文件夹
			if a[2:len(folder) + 2] == folder:
				ignore_folder_flag = True
				break
		#################################################

		for file in c:
			if '.py' in file:
				f_path = os.path.join(a, file)[2:]
				print(f_path, os.path.join(build_dir, a[2:]))

				if f_path in args.ignore or ignore_folder_flag:
					shutil.copy(f_path,
								os.path.join(os.getcwd(), os.path.join(build_dir, a[2:])))

			elif '.' not in file or file.split('.')[-1] not in ['py','pyc']:
				shutil.copy(os.path.join(os.getcwd(), os.path.join(a, file)[2:]),
							os.path.join(os.getcwd(), os.path.join(build_dir, a[2:])))

	return True

def recompile():
	"""
	    ** Function：when the cythonize() compile make some errors, recompile by tmp_dir/.o file
	    ** authon：dq
	    ** create date：19-12-25
	"""
	if os.path.exists(build_dir):
		shutil.rmtree(build_dir)

	for a,b,c in os.walk(build_tmp_dir):
		if args.dirname not in a:
			continue

		target_path = build_dir+'/'+ args.dirname+'/'+a.split(args.dirname, maxsplit=1)[1][1:]
		if not os.path.exists(target_path):
			os.makedirs(target_path)		# so生成目录

		for file in c:
			f_source_path = args.dirname + os.path.join(a, file.split('.')[0] + '.py').split(args.dirname, maxsplit=1)[1]

			if f_source_path not in args.ignore:
				if '.' in file and file.split('.')[-1] == 'o':
					file_path = os.path.join(a,file)
					target_path = build_dir + '/' + f_source_path
					print('\033[0;34m gcc -shared %s -o %s.so\033[0m' % (file_path,  target_path[:-3]))
					os.system('gcc -shared %s -o %s.so' % (file_path, target_path[:-3]))

			else:
				target_path = build_dir+'/'+ f_source_path
				print('\033[1;43m copy main func %s --> %s\033[0m' % (f_source_path, target_path))
				os.system('cp %s %s' % (f_source_path, target_path))



if __name__ == "__main__":
	get_pyfiles()




