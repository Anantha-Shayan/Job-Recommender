x = {'Greet':["Hi", 'Bye']}
y = {'Greet':["Hi"]}

print(list(set(x.get('Greet')) - set(y['Greet'])))