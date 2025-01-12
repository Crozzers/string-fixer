use libcst_native::AssignTargetExpression;
use libcst_native::Codegen;
use libcst_native::CodegenState;
use libcst_native::DelTargetExpression;
use libcst_native::Expression;
use libcst_native::List;
use libcst_native::SimpleString;
use libcst_native::SmallStatement;
use libcst_native::Statement;
use libcst_native::Tuple;
use libcst_native::Element;
use libcst_native as cst;
use typed_arena::Arena;

pub fn replace_quotes(code: &str) -> String {
    let arena: Arena<String> = Arena::new();

    let mut module = cst::parse_module(code, None).expect("failed to parse module");


    for statement in module.body.iter_mut() {
        match statement {
            Statement::Compound(_stmt) => {}
            Statement::Simple(stmt) => {
                for simple_stmt in stmt.body.iter_mut() {
                    process_small_statement(simple_stmt, &arena);
                }
            }
        }
    }


    let mut state = CodegenState::default();
    module.codegen(&mut state);

    return state.tokens;
}


fn process_small_statement<'a>(statement: &mut SmallStatement<'a>, arena: &'a Arena<String>) {
    match statement {
        SmallStatement::Return(stmt) => {
            if let Some(value) = &mut stmt.value {
                process_expression( value, arena);
            }
        }
        SmallStatement::Expr(stmt) => {
            process_expression(&mut stmt.value, arena);
        }
        SmallStatement::Assert(stmt) => {
            process_expression(&mut stmt.test, arena);
            if let Some(msg) = &mut stmt.msg {
                process_expression(msg, arena);
            }
        }
        SmallStatement::Assign(stmt) => {
            process_expression(&mut stmt.value, arena);
        }
        SmallStatement::AnnAssign(stmt) => {
            process_assign_target_expression(&mut stmt.target, arena);
        }
        SmallStatement::Raise(stmt) => {
            if let Some(ref mut expr) = stmt.exc {
                process_expression(expr, arena);
            }
            if let Some(ref mut cause) = stmt.cause {
                process_expression(&mut cause.item, arena);
            }
        }
        SmallStatement::AugAssign(stmt) => {
            process_assign_target_expression(&mut stmt.target, arena);
            process_expression(&mut stmt.value, arena);
        }
        SmallStatement::Del(stmt) => {
            process_del_target_expression(&mut stmt.target, arena)
        }
        SmallStatement::TypeAlias(stmt) => {
            process_expression(&mut stmt.value, arena);
            if let Some(ref mut type_parameters) = stmt.type_parameters {
                for param in type_parameters.params.iter_mut() {
                    match param.param {
                        cst::TypeVarLike::TypeVar(ref mut tv) => {
                            if let Some(ref mut bound) = &mut tv.bound {
                                process_expression(bound, arena);
                            }
                        }
                        _ => {}
                    }

                    if let Some(ref mut default) = param.default {
                        process_expression(default, arena);
                    }
                }
            }
        }
        _ => {}
    }
}


fn process_del_target_expression<'a>(target: &mut cst::DelTargetExpression<'a>, arena: &'a Arena<String>) {
    match target {
        DelTargetExpression::Attribute(target) => {
            process_expression(&mut(*target.value), arena);
        }
        DelTargetExpression::Tuple(target) => {
            process_tuple(&mut **target, arena);
        }
        DelTargetExpression::List(target) => {
            process_tuple(&mut **target, arena);
        }
        DelTargetExpression::Subscript(target) => {
            process_subscript(target, arena);
        }
        _ => {}
    }
}


fn process_assign_target_expression<'a>(target: &mut cst::AssignTargetExpression<'a>, arena: &'a Arena<String>) {
    match target {
        AssignTargetExpression::Attribute(target) => {
            process_expression(&mut(*target.value), arena);
        }
        AssignTargetExpression::StarredElement(target) => {
            process_expression(&mut(*target.value), arena);
        }
        AssignTargetExpression::Tuple(target) => {
            process_tuple(&mut **target, arena);
        }
        AssignTargetExpression::List(target) => {
            process_tuple(&mut **target, arena);
        }
        AssignTargetExpression::Subscript(target) => {
            process_subscript(target, arena);
        }
        _ => {}
    }
}


fn process_subscript<'a>(target: &mut cst::Subscript<'a>, arena: &'a Arena<String>) {
    process_expression(&mut target.value, arena);
    for elem in target.slice.iter_mut() {
        match &mut elem.slice {
            cst::BaseSlice::Index(slice) => {
                process_expression(&mut slice.value, arena);
            }
            cst::BaseSlice::Slice(slice) => {
                if let Some(ref mut lower) = &mut slice.lower {
                    process_expression(lower, arena);
                }
                if let Some(ref mut upper) = &mut slice.upper {
                    process_expression(upper, arena);
                }
                if let Some(ref mut step) = &mut slice.step {
                    process_expression(step, arena);
                }
            }
        }
    }
}


trait HasElements<'a> {
    fn get_elements_mut(&mut self) -> &mut Vec<Element<'a>>;
}

impl<'a> HasElements<'a> for Tuple<'a> {
    fn get_elements_mut(&mut self) -> &mut Vec<Element<'a>> {
        return &mut self.elements
    }
}

impl<'a> HasElements<'a> for List<'a> {
    fn get_elements_mut(&mut self) -> &mut Vec<Element<'a>> {
        return &mut self.elements
    }
}

fn process_tuple<'a, T: HasElements<'a>>(tuple: &mut T, arena: &'a Arena<String>) {
    for element in tuple.get_elements_mut().iter_mut() {
        match element {
            Element::Simple {ref mut value, comma: _} => {
                process_expression(value, arena);
            }
            Element::Starred(elem) => {
                process_expression(&mut(*elem.value), arena);
            }
        }
    }
}


fn process_expression<'a>(expression: &mut Expression<'a>, arena: &'a Arena<String>) {
    match expression {
        Expression::SimpleString(expr) => {
            process_simple_string(expr, arena);
        }
        _ => {}
    }
}


fn process_simple_string<'a>(string: &mut SimpleString<'a>, arena: &'a Arena<String>) {
    let strval = string.value;
    println!("SS found: {}", strval);

    let replaced = strval.replace('"', "'");
    let replaced_ref = arena.alloc(replaced);
    string.value = replaced_ref;

    println!("SS replaced: {}", string.value)
}

