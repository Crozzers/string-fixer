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
        process_statement(statement, &arena);
    }


    let mut state = CodegenState::default();
    module.codegen(&mut state);

    return state.tokens;
}


fn process_statement<'a>(statement: &mut cst::Statement<'a>, arena: &'a Arena<String>) {
    match statement {
        Statement::Simple(stmt) => {
            for simple_stmt in stmt.body.iter_mut() {
                process_small_statement(simple_stmt, &arena);
            }
        }
        Statement::Compound(stmt) => {
            match stmt {
                cst::CompoundStatement::FunctionDef(stmt) =>
                    process_functiondef(stmt, arena),

                cst::CompoundStatement::If(stmt) =>
                    process_if(stmt, arena),

                cst::CompoundStatement::For(stmt) => {
                    process_assign_target_expression(&mut stmt.target, arena);
                    process_expression(&mut stmt.iter, arena);
                    process_suite(&mut stmt.body, arena);
                    if let Some(ref mut else_stmt) = stmt.orelse {
                        process_suite(&mut else_stmt.body, arena);
                    }
                }
                cst::CompoundStatement::While(stmt) => {
                    process_expression(&mut stmt.test, arena);
                    process_suite(&mut stmt.body, arena);
                    if let Some(ref mut else_stmt) = stmt.orelse {
                        process_suite(&mut else_stmt.body, arena);
                    }
                }
                cst::CompoundStatement::ClassDef(stmt) => {
                    if let Some(ref mut type_params) = stmt.type_parameters {
                        process_type_parameter( type_params, arena);
                    }
                    process_suite(&mut stmt.body, arena);

                    for arg in stmt.bases.iter_mut().chain(stmt.keywords.iter_mut()) {
                        process_expression(&mut arg.value, arena);
                    }

                    for decorator in stmt.decorators.iter_mut() {
                        process_expression(&mut decorator.decorator, arena)
                    }
                }
                cst::CompoundStatement::Try(stmt) => {
                    process_suite(&mut stmt.body, arena);
                    for handler in stmt.handlers.iter_mut() {
                        process_suite(&mut handler.body, arena);
                        if let Some(ref mut rtype) = handler.r#type {
                            process_expression(rtype, arena);
                        }
                        if let Some(ref mut asname) = handler.name {
                            process_assign_target_expression(&mut asname.name, arena);
                        }
                    }
                    if let Some(ref mut orelse) = stmt.orelse {
                        process_suite(&mut orelse.body, arena);
                    }
                    if let Some(ref mut finally) = stmt.finalbody {
                        process_suite(&mut finally.body, arena);
                    }
                }
                cst::CompoundStatement::TryStar(stmt) => {
                    process_suite(&mut stmt.body, arena);
                    for handler in stmt.handlers.iter_mut() {
                        process_suite(&mut handler.body, arena);
                        process_expression(&mut handler.r#type, arena);
                        if let Some(ref mut asname) = handler.name {
                            process_assign_target_expression(&mut asname.name, arena);
                        }
                    }
                    if let Some(ref mut orelse) = stmt.orelse {
                        process_suite(&mut orelse.body, arena);
                    }
                    if let Some(ref mut finally) = stmt.finalbody {
                        process_suite(&mut finally.body, arena);
                    }
                }
                cst::CompoundStatement::With(stmt) => {
                    for item in stmt.items.iter_mut() {
                        process_expression(&mut item.item, arena);
                        if let Some(ref mut asname) = item.asname {
                            process_assign_target_expression(&mut asname.name, arena);
                        }

                    }
                    process_suite(&mut stmt.body, arena);
                }
                cst::CompoundStatement::Match(stmt) =>
                    process_match(stmt, arena)

            }
        }
    }
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
                process_type_parameter(type_parameters, arena);
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


fn process_type_parameter<'a>(type_parameters: &mut cst::TypeParameters<'a>, arena: &'a Arena<String>) {
    for type_param in type_parameters.params.iter_mut() {
        match type_param.param {
            cst::TypeVarLike::TypeVar(ref mut tv) => {
                if let Some(ref mut bound) = &mut tv.bound {
                    process_expression(bound, arena);
                }
            }
            _ => {}
        }

        if let Some(ref mut default) = type_param.default {
            process_expression(default, arena);
        }
    }
}


fn process_param<'a>(param: &mut cst::Param<'a>, arena: &'a Arena<String>) {
    if let Some(ref mut annotation) = param.annotation {
        process_expression(&mut annotation.annotation, arena);
    }

    if let Some(ref mut default) = param.default {
        process_expression(default, arena);
    }
}


fn process_parameters<'a>(parameters: &mut cst::Parameters<'a>, arena: &'a Arena<String>) {
    for param in parameters.params.iter_mut() {
        process_param(param, arena);
    }

    if let Some(ref mut star_arg) = parameters.star_arg {
        match star_arg {
            cst::StarArg::Param(star_arg) => {
                process_param(star_arg, arena);
            }
            _ => {}
        }
    }

    for kwonly_param in parameters.kwonly_params.iter_mut() {
        process_param(kwonly_param, arena);
    }

    if let Some(ref mut star_kwarg) = parameters.star_kwarg {
        process_param(star_kwarg, arena);
    }

    for posonly_param in parameters.posonly_params.iter_mut() {
        process_param(posonly_param, arena);
    }
}


fn process_functiondef<'a>(functiondef: &mut cst::FunctionDef<'a>, arena: &'a Arena<String>) {
    if let Some(ref mut type_parameters) = functiondef.type_parameters {
        process_type_parameter(type_parameters, &arena);
    }

    process_parameters(&mut functiondef.params, &arena);

    process_suite(&mut functiondef.body, arena);

    for decorator in functiondef.decorators.iter_mut() {
        process_expression(&mut decorator.decorator, arena);
    }

    if let Some(ref mut returns) = functiondef.returns {
        process_expression(&mut returns.annotation, arena);
    }
}


fn process_suite<'a>(suite: &mut cst::Suite<'a>, arena: &'a Arena<String>) {
    match suite {
        cst::Suite::IndentedBlock(block) => {
            for statement in block.body.iter_mut() {
                process_statement(statement, arena);
            }
        }
        cst::Suite::SimpleStatementSuite(suite) => {
            for statement in suite.body.iter_mut() {
                process_small_statement(statement, arena);
            }
        }
    }
}


fn process_if<'a>(if_stmt: &mut cst::If<'a>, arena: &'a Arena<String>) {
    process_expression(&mut if_stmt.test, arena);
    process_suite(&mut if_stmt.body, arena);

    match if_stmt.orelse {
        Some(ref mut or_else) => match or_else.as_mut() {
            cst::OrElse::Elif(elif) => {
                process_if( elif, arena);
            }
            cst::OrElse::Else(else_stmt) => {
                process_suite(&mut else_stmt.body, arena);
            }
        }
        None => {}
    }
}


fn process_match<'a>(match_stmt: &mut cst::Match<'a>, arena: &'a Arena<String>) {
    process_expression(&mut match_stmt.subject, arena);
    for case in match_stmt.cases.iter_mut() {
        process_matchpattern(&mut case.pattern, arena);

        if let Some(ref mut guard) = case.guard {
            process_expression(guard, arena);
        }
    }
}


fn process_matchpattern<'a>(pattern: &mut cst::MatchPattern<'a>, arena: &'a Arena<String>) {
    match pattern {
        cst::MatchPattern::Value(value) => {
            process_expression(&mut value.value, arena);
        }
        cst::MatchPattern::Sequence(seq) => {
            match seq {
                cst::MatchSequence::MatchList(list) => {
                    for list_pattern in list.patterns.iter_mut() {
                        process_starrable_match_sequence_element(list_pattern, arena)
                    }
                }
                cst::MatchSequence::MatchTuple(tuple) => {
                    for tuple_pattern in tuple.patterns.iter_mut() {
                        process_starrable_match_sequence_element(tuple_pattern, arena);
                    }
                }
            }
        }
        cst::MatchPattern::Mapping(mapping) => {
            for element in mapping.elements.iter_mut() {
                process_expression(&mut element.key, arena);
                process_matchpattern(&mut element.pattern, arena);
            }
        }
        cst::MatchPattern::Class(class) => {
            match class.cls {
                cst::NameOrAttribute::A(ref mut attr) => {
                    process_expression(&mut attr.value, arena);
                }
                _ => {}
            }
            for pattern in class.patterns.iter_mut() {
                process_matchpattern(&mut pattern.value, arena);
            }
            for kwd in class.kwds.iter_mut() {
                process_matchpattern(&mut kwd.pattern, arena);
            }
        }
        cst::MatchPattern::As(match_as) => {
            if let Some(ref mut mp) = match_as.pattern {
                process_matchpattern(mp, arena);
            }
        }
        cst::MatchPattern::Or(match_or) => {
            for element in match_or.patterns.iter_mut() {
                process_matchpattern(&mut element.pattern, arena);
            }
        }
        _ => {}
    }
}


fn process_starrable_match_sequence_element<'a>(element: &mut cst::StarrableMatchSequenceElement<'a>, arena: &'a Arena<String>) {
    match element {
        cst::StarrableMatchSequenceElement::Simple(element) => {
            process_matchpattern(&mut element.value, arena);
        }
        _ => {}
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

